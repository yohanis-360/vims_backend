"""
API views for User management.
Implements scope-based filtering and caching for performance.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import User, Role, RoleAssignment, PasswordResetToken
from .serializers import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer,
    RoleSerializer, RoleAssignmentSerializer, PasswordChangeSerializer,
    LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User CRUD operations with scope filtering.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'full_name', 'email', 'phone']
    ordering_fields = ['created_at', 'username', 'full_name']
    filterset_fields = ['status', 'is_active']
    lookup_field = 'user_id'  # Use user_id instead of pk for lookups
    lookup_url_kwarg = 'user_id'  # URL parameter name
    
    def get_object(self):
        """Override to use user_id lookup."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        filter_kwargs = {self.lookup_field: lookup_value}
        obj = get_object_or_404(self.get_queryset(), **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj
    
    def get_queryset(self):
        """Filter users by requesting user's scope."""
        user_scope = self.request.user.get_scope_data()
        
        # Cache key based on user scope
        cache_key = f"users_list:{user_scope['type']}:{':'.join(map(str, user_scope['ids']))}"
        
        queryset = cache.get(cache_key)
        if not queryset:
            queryset = User.objects.prefetch_related(
                'role_assignments__role'
            )
            
            # Apply scope filtering
            if user_scope['type'] != 'National':
                queryset = queryset.filter(
                    role_assignments__scope_ids__overlap=user_scope['ids'],
                    role_assignments__status='Active'
                ).distinct()
            
            # Cache for 5 minutes
            cache.set(cache_key, queryset, timeout=300)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        return UserDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new user with audit logging."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Invalidate cache
        cache.delete_pattern('users_list:*')
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=request.user,
            action='USER_CREATED',
            resource_type='User',
            resource_id=user.user_id,
            details={'username': user.username}
        )
        
        # Return detailed user data
        response_serializer = UserDetailSerializer(user)
        response_data = response_serializer.data
        
        # Debug: Check if temporary_password exists
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[DEBUG] Checking temporary_password for user {user.username}")
        logger.info(f"[DEBUG] hasattr(user, 'temporary_password'): {hasattr(user, 'temporary_password')}")
        if hasattr(user, 'temporary_password'):
            logger.info(f"[DEBUG] user.temporary_password value: {user.temporary_password}")
        
        # Include temporary password if it was generated (for inspectors)
        if hasattr(user, 'temporary_password') and user.temporary_password:
            response_data['temporary_password'] = user.temporary_password
            # Log the temporary password in backend logs (also logged in serializer)
            logger.info(
                f"[VIEW] User created with temporary password - User ID: {user.user_id}, "
                f"Username: {user.username}, Email: {user.email}, "
                f"Temporary Password: {user.temporary_password}"
            )
            
            # Send email with temporary password to admin
            try:
                from .utils import send_temporary_password_email
                logger.info(f"[EMAIL] Calling send_temporary_password_email for user {user.username}")
                send_temporary_password_email(user, user.temporary_password)
                logger.info(f"[EMAIL] Email sending function completed for user {user.username}")
            except Exception as e:
                logger.error(f"[EMAIL] Failed to send temporary password email: {str(e)}", exc_info=True)
                # Don't fail user creation if email fails, but log the error
        else:
            logger.info(f"[DEBUG] No temporary password found for user {user.username}")
        
        headers = self.get_success_headers(response_data)
        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, user_id=None):
        """Change user password."""
        # Allow users to change their own password even if not in filtered queryset
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        # If user is changing their own password, use request.user directly
        # This bypasses scope filtering and avoids database lookup issues
        if str(request.user.user_id) == str(lookup_value):
            user = request.user
        else:
            # For other users, use normal scope filtering
            user = self.get_object()
        
        serializer = PasswordChangeSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data['old_password']):
                return Response(
                    {'error': 'Incorrect old password'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            from django.utils import timezone
            user.set_password(serializer.data['new_password'])
            user.password_changed_at = timezone.now()
            user.save()
            
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='assign_role')
    def assign_role(self, request, user_id=None):
        """Assign a role to user."""
        user = self.get_object()
        
        # Get role from request data (role_id)
        role_id = request.data.get('role')
        if not role_id:
            return Response(
                {'error': 'role field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from .models import Role
            role = Role.objects.get(role_id=role_id)
        except Role.DoesNotExist:
            return Response(
                {'error': f'Role with ID {role_id} does not exist'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RoleAssignmentSerializer(
            data=request.data,
            context={
                'user': user,
                'role': role,
                'assigned_by': request.user
            }
        )
        
        if serializer.is_valid():
            # TODO: Check delegation policy
            assignment = serializer.save()
            
            # Invalidate cache
            cache.delete(f'user_scope:{user.user_id}')
            cache.delete_pattern('users_list:*')
            cache.delete_pattern('dashboard_overview:*')
            cache.delete_pattern('centers_list:*')
            
            # Log action
            from apps.security.utils import log_action
            log_action(
                user=request.user,
                action='ROLE_ASSIGNED',
                resource_type='User',
                resource_id=user.user_id,
                details={'role_id': assignment.role.role_id, 'scope': assignment.scope_type}
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, user_id=None):
        """Suspend a user account."""
        user = self.get_object()
        
        if user.status == 'Suspended':
            return Response(
                {'error': 'User is already suspended'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.status = 'Suspended'
        user.is_active = False
        user.save(update_fields=['status', 'is_active'])
        
        # Invalidate cache
        cache.delete_pattern('users_list:*')
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=request.user,
            action='USER_SUSPENDED',
            resource_type='User',
            resource_id=user.user_id,
            details={'username': user.username}
        )
        
        return Response({'message': 'User suspended successfully'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, user_id=None):
        """Activate a suspended user account."""
        user = self.get_object()
        
        if user.status == 'Active':
            return Response(
                {'error': 'User is already active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.status = 'Active'
        user.is_active = True
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.save(update_fields=['status', 'is_active', 'failed_login_attempts', 'account_locked_until'])
        
        # Invalidate cache
        cache.delete_pattern('users_list:*')
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=request.user,
            action='USER_ACTIVATED',
            resource_type='User',
            resource_id=user.user_id,
            details={'username': user.username}
        )
        
        return Response({'message': 'User activated successfully'})
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete a user (set status to Disabled)."""
        user = self.get_object()
        
        # Don't allow deleting superusers
        if user.is_superuser:
            return Response(
                {'error': 'Cannot delete superuser accounts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete by setting status to Disabled
        user.status = 'Disabled'
        user.is_active = False
        user.save(update_fields=['status', 'is_active'])
        
        # Invalidate cache
        cache.delete_pattern('users_list:*')
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=request.user,
            action='USER_DELETED',
            resource_type='User',
            resource_id=user.user_id,
            details={'username': user.username}
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Role CRUD operations.
    """
    queryset = Role.objects.filter(enabled=True)
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'role_id'
    
    def list(self, request, *args, **kwargs):
        """List all available roles with caching."""
        cache_key = 'roles_list'
        
        roles = cache.get(cache_key)
        if not roles:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            roles = serializer.data
            cache.set(cache_key, roles, timeout=3600)  # Cache for 1 hour
        
        return Response(roles)
    
    def create(self, request, *args, **kwargs):
        """Create a new role."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        
        # Invalidate cache
        cache.delete('roles_list')
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=request.user,
            action='ROLE_CREATED',
            resource_type='Role',
            resource_id=role.role_id,
            details={'role_name': role.role_name_en}
        )
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        """Update an existing role."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Invalidate cache
        cache.delete('roles_list')
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=request.user,
            action='ROLE_UPDATED',
            resource_type='Role',
            resource_id=instance.role_id,
            details={'role_name': instance.role_name_en}
        )
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Disable a role (soft delete)."""
        instance = self.get_object()
        
        # Soft delete by disabling
        instance.enabled = False
        instance.save(update_fields=['enabled'])
        
        # Invalidate cache
        cache.delete('roles_list')
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=request.user,
            action='ROLE_DELETED',
            resource_type='Role',
            resource_id=instance.role_id,
            details={'role_name': instance.role_name_en}
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(viewsets.ViewSet):
    """
    Custom login view with JWT token generation.
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Authenticate user and return JWT tokens."""
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.data['username']
            password = request.data['password']
            machine_id = request.data.get('machineId', None)
            
            user = authenticate(username=username, password=password)
            
            if user is None:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if not user.is_active or user.status != 'Active':
                return Response(
                    {'error': 'Account is not active'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if password change is required (password_changed_at is None)
            requires_password_change = user.password_changed_at is None
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Update last login
            from django.utils import timezone
            user.last_login_at = timezone.now()
            user.failed_login_attempts = 0
            user.save(update_fields=['last_login_at', 'failed_login_attempts'])
            
            # Log action
            from apps.security.utils import log_action
            log_action(
                user=user,
                action='USER_LOGIN',
                resource_type='Auth',
                resource_id=user.user_id,
                details={'machine_id': machine_id}
            )
            
            # Get user's primary role and scope data
            from .models import RoleAssignment
            primary_role_assignment = RoleAssignment.objects.filter(
                user=user,
                status='Active'
            ).order_by('-assigned_at').first()
            
            primary_role = None
            if primary_role_assignment:
                primary_role = {
                    'role': {
                        'role_id': primary_role_assignment.role.role_id,
                        'role_name_en': primary_role_assignment.role.role_name_en,
                    },
                    'scope_type': primary_role_assignment.scope_type,
                    'scope_ids': primary_role_assignment.scope_ids,
                }
            
            user_data = UserDetailSerializer(user).data
            user_data['requires_password_change'] = requires_password_change
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_data,
                'requires_password_change': requires_password_change,
                'primary_role': primary_role,
                'machineId': machine_id
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='machine/verify')
    def verify_machine(self, request):
        """Verify inspector machine by MAC address and certificate."""
        mac_address = request.data.get('macAddress')
        certificate_serial = request.data.get('certificateSerial')
        
        if not mac_address:
            return Response(
                {'error': 'MAC address is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implement actual machine verification against registered machines database
        # For now, returning mock verification (accept machines starting with 00:1B:44)
        trusted = mac_address.upper().startswith('00:1B:44')
        machine_id = f"M-{mac_address.replace(':', '')}" if trusted else None
        
        return Response({
            'trusted': trusted,
            'machineId': machine_id,
            'certificateSerial': certificate_serial,
            'message': 'Machine verified successfully' if trusted else 'Machine not registered'
        })
    
    @action(detail=False, methods=['post'], url_path='machine/handshake')
    def machine_handshake(self, request):
        """Initialize handshake for machine-inspector communication."""
        machine_id = request.data.get('machineId')
        mac_address = request.data.get('macAddress')
        
        if not machine_id or not mac_address:
            return Response(
                {'error': 'Machine ID and MAC address are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Store machine session for tracking
        return Response({
            'status': 'INITIATED',
            'machineId': machine_id,
            'macAddress': mac_address,
            'sessionId': f"SES-{machine_id}-{int(timezone.now().timestamp())}",
            'timestamp': timezone.now().isoformat()
        })


class ForgotPasswordView(viewsets.ViewSet):
    """
    ViewSet for forgot password functionality.
    """
    permission_classes = [AllowAny]  # Public endpoint
    
    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        """
        Request password reset. Sends reset token to user's email.
        """
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        username = serializer.validated_data.get('username')
        
        # Find user by email or username
        try:
            if email:
                user = User.objects.get(email=email, is_active=True)
            elif username:
                user = User.objects.get(username=username, is_active=True)
            else:
                return Response(
                    {'error': 'Email or username is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            # Don't reveal if user exists or not (security best practice)
            return Response({
                'message': 'If the email/username exists, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)
        
        # Generate reset token
        import secrets
        from datetime import timedelta
        
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=24)  # Token valid for 24 hours
        
        # Create or update reset token (invalidate old tokens for this user)
        PasswordResetToken.objects.filter(user=user, used=False).update(used=True, used_at=timezone.now())
        
        reset_token = PasswordResetToken.objects.create(
            token=token,
            user=user,
            expires_at=expires_at
        )
        
        # Send email with reset link
        from .utils import send_password_reset_email
        send_password_reset_email(user, token)
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=user,
            action='PASSWORD_RESET_REQUESTED',
            resource_type='User',
            resource_id=user.user_id,
            details={'username': user.username, 'email': user.email}
        )
        
        return Response({
            'message': 'If the email/username exists, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        """
        Reset password using token.
        """
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data.get('token')
        new_password = serializer.validated_data.get('new_password')
        
        # Find and validate token
        try:
            reset_token = PasswordResetToken.objects.get(token=token, used=False)
        except PasswordResetToken.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired reset token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if token is valid (not expired)
        if not reset_token.is_valid():
            reset_token.used = True
            reset_token.used_at = timezone.now()
            reset_token.save()
            return Response(
                {'error': 'Reset token has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update password
        user = reset_token.user
        user.set_password(new_password)
        user.password_changed_at = timezone.now()
        user.failed_login_attempts = 0  # Reset failed login attempts
        user.account_locked_until = None  # Unlock account if locked
        user.save()
        
        # Mark token as used
        reset_token.used = True
        reset_token.used_at = timezone.now()
        reset_token.save()
        
        # Log action
        from apps.security.utils import log_action
        log_action(
            user=user,
            action='PASSWORD_RESET_COMPLETED',
            resource_type='User',
            resource_id=user.user_id,
            details={'username': user.username}
        )
        
        return Response({
            'message': 'Password has been reset successfully. You can now login with your new password.'
        }, status=status.HTTP_200_OK)


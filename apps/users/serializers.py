"""
Serializers for User, Role, and RoleAssignment models.
"""
import logging
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Role, RoleAssignment, DelegationPolicy

logger = logging.getLogger(__name__)


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    class Meta:
        model = Role
        fields = [
            'role_id', 'role_name_en', 'role_name_am',
            'role_category', 'default_scope_type',
            'is_sensitive_role', 'two_person_approval_required',
            'permissions', 'enabled', 'version'
        ]
        read_only_fields = ['role_id']


class RoleAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for RoleAssignment model."""
    
    role_name = serializers.CharField(source='role.role_name_en', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    role = serializers.CharField(write_only=True)  # Accept role_id as string
    
    class Meta:
        model = RoleAssignment
        fields = [
            'role_assignment_id', 'user', 'role', 'role_name',
            'user_name', 'scope_type', 'scope_ids', 'status',
            'approval_required', 'approval_status', 'approved_by',
            'approved_at', 'effective_from', 'effective_to',
            'assigned_by', 'assigned_at'
        ]
        read_only_fields = [
            'role_assignment_id', 'user', 'assigned_by', 'assigned_at',
            'approved_by', 'approved_at'
        ]
    
    def create(self, validated_data):
        """Create role assignment with auto-generated ID."""
        import uuid
        from django.utils import timezone
        from .models import Role
        
        # Get user and assigned_by from context (set by view)
        user = self.context.get('user')
        assigned_by = self.context.get('assigned_by')
        
        # Get role_id from validated_data and resolve to Role object
        role_id = validated_data.pop('role')
        try:
            role = Role.objects.get(role_id=role_id)
        except Role.DoesNotExist:
            raise serializers.ValidationError({'role': f'Role with ID {role_id} does not exist.'})
        
        if not user:
            raise serializers.ValidationError("User is required")
        
        # Generate role_assignment_id
        role_assignment_id = f"RA-{user.user_id}-{role.role_id}-{uuid.uuid4().hex[:8].upper()}"
        
        # Create the assignment
        logger.info(f"Creating role assignment for user {user.username}")
        logger.info(f"Role: {role.role_id}, Scope type: {validated_data.get('scope_type')}, Scope IDs: {validated_data.get('scope_ids')}")
        
        assignment = RoleAssignment.objects.create(
            role_assignment_id=role_assignment_id,
            user=user,
            role=role,
            assigned_by=assigned_by,
            assigned_at=timezone.now(),
            **validated_data
        )
        
        logger.info(f"Created assignment: {assignment.role_assignment_id}, Status: {assignment.status}, Scope IDs: {assignment.scope_ids}")
        return assignment


class UserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user lists."""
    
    primary_role = serializers.SerializerMethodField()
    # institution_name = serializers.CharField(
    #     source='institution.institution_name_en',
    #     read_only=True
    # )
    
    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'full_name', 'email', 'phone',
            'job_title', 'primary_role',
            'status', 'is_active', 'last_login_at', 'created_at'
        ]
    
    def get_primary_role(self, obj):
        """Get primary role assignment."""
        role = obj.get_primary_role()
        if role:
            return {
                'role_id': role.role.role_id,
                'role_name': role.role.role_name_en,
                'scope_type': role.scope_type
            }
        return None


class UserDetailSerializer(serializers.ModelSerializer):
    """Full serializer for user details."""
    
    role_assignments = RoleAssignmentSerializer(many=True, read_only=True)
    # institution_name = serializers.CharField(
    #     source='institution.institution_name_en',
    #     read_only=True
    # )
    scope_data = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'user_id', 'username', 'full_name', 'email', 'phone',
            'job_title',  # 'institution', 'institution_name',
            'status', 'is_active', 'mfa_enrolled',
            'last_login_at', 'password_changed_at',
            'created_at', 'updated_at', 'created_by',
            'role_assignments', 'scope_data'
        ]
        read_only_fields = [
            'user_id', 'last_login_at', 'password_changed_at',
            'created_at', 'updated_at', 'created_by'
        ]
    
    def get_scope_data(self, obj):
        """Get user's scope information."""
        return obj.get_scope_data()


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    
    password = serializers.CharField(
        write_only=True,
        required=False,  # Not required - will generate if not provided
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'phone', 'full_name',
            'job_title', 'status',
            'password', 'password_confirm'
        ]
    
    def validate(self, attrs):
        """Validate password confirmation if provided."""
        password = attrs.get('password')
        password_confirm = attrs.pop('password_confirm', None)
        
        if password and password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError({
                    'password_confirm': 'Passwords do not match.'
                })
        elif password and not password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Password confirmation is required.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password or temporary password."""
        import uuid
        import secrets
        import string
        
        password = validated_data.pop('password', None)
        
        # Generate temporary password if not provided (for inspectors)
        temporary_password = None
        if not password:
            # Generate a secure temporary password: 12 characters with mix of letters, digits, and symbols
            alphabet = string.ascii_letters + string.digits + '!@#$%'
            temporary_password = ''.join(secrets.choice(alphabet) for _ in range(12))
            password = temporary_password
            
            # Log the temporary password for admin reference
            logger.info(
                f"Temporary password generated for user: username={validated_data.get('username')}, "
                f"email={validated_data.get('email')}, temporary_password={temporary_password}"
            )
        
        # Generate user_id
        validated_data['user_id'] = f"U-{uuid.uuid4().hex[:8].upper()}"
        
        user = User.objects.create_user(password=password, **validated_data)
        
        # Set created_by from context
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user.created_by = request.user
            user.save()
        
        # Store temporary password in user object for response (not saved to DB)
        # IMPORTANT: Set this BEFORE returning, so the view can access it
        if temporary_password:
            user.temporary_password = temporary_password
            # Log the temporary password in backend logs (after user is created)
            logger.info(
                f"[SERIALIZER] User created with temporary password - User ID: {user.user_id}, "
                f"Username: {user.username}, Email: {user.email}, "
                f"Temporary Password: {temporary_password}"
            )
            logger.info(f"[SERIALIZER] Set user.temporary_password = {temporary_password}")
        else:
            logger.info(f"[SERIALIZER] No temporary password generated for user {user.username}")
        
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request."""
    
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=False)


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for password reset with token."""
    
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs


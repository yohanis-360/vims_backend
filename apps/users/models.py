"""
User and Role models for VIMS Backend.
Implements role-based access control with scope filtering.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """Custom user manager."""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not username:
            raise ValueError('Users must have a username')
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', 'Active')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for VIMS.
    Supports multiple role assignments with scope filtering.
    """
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
        ('Disabled', 'Disabled'),
        ('Pending', 'Pending Activation'),
    ]
    
    # Basic Information
    user_id = models.CharField(max_length=50, unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?\d{10,15}$')],
        db_index=True
    )
    full_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=100, blank=True)
    
    # Institution
    # TODO: Uncomment after governance.Institution model is created
    # institution = models.ForeignKey(
    #     'governance.Institution',
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     related_name='users'
    # )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending', db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Security
    mfa_enrolled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users'
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name']
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['username', 'email']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.username})"
    
    def get_active_role_assignments(self):
        """Get all active role assignments for this user."""
        return self.role_assignments.filter(status='Active')
    
    def get_primary_role(self):
        """Get the primary (first active) role assignment."""
        return self.role_assignments.filter(status='Active').first()
    
    def has_role(self, role_id):
        """Check if user has a specific role."""
        return self.role_assignments.filter(
            role__role_id=role_id,
            status='Active'
        ).exists()
    
    def get_scope_data(self):
        """Get user's scope information for filtering."""
        import logging
        logger = logging.getLogger(__name__)
        
        primary_role = self.get_primary_role()
        if not primary_role:
            logger.warning(f"User {self.username} has no primary role")
            return {'type': 'None', 'ids': []}
        
        scope_data = {
            'type': primary_role.scope_type,
            'ids': primary_role.scope_ids or [],
            'role_id': primary_role.role.role_id,
            'role_name': primary_role.role.role_name_en,
        }
        
        logger.info(f"User {self.username} scope_data: {scope_data}")
        return scope_data


class Role(models.Model):
    """
    Role definitions for RBAC.
    """
    
    ROLE_CATEGORIES = [
        ('Admin', 'Admin'),
        ('Audit', 'Audit'),
        ('Operations', 'Operations'),
        ('Enforcement', 'Enforcement'),
        ('ReadOnly', 'Read Only'),
    ]
    
    SCOPE_TYPES = [
        ('National', 'National'),
        ('Regional', 'Regional'),
        ('Zone', 'Zone'),
        ('SubCity', 'Sub-City'),
        ('Woreda', 'Woreda'),
        ('Center', 'Center'),
    ]
    
    role_id = models.CharField(max_length=50, unique=True, primary_key=True)
    role_name_en = models.CharField(max_length=100)
    role_name_am = models.CharField(max_length=100, blank=True)
    role_category = models.CharField(max_length=20, choices=ROLE_CATEGORIES)
    default_scope_type = models.CharField(max_length=20, choices=SCOPE_TYPES)
    
    # Security
    is_sensitive_role = models.BooleanField(default=False)
    two_person_approval_required = models.BooleanField(default=False)
    
    # Permissions (JSON field for flexibility)
    permissions = models.JSONField(default=list)
    
    # Status
    enabled = models.BooleanField(default=True)
    version = models.CharField(max_length=10, default='1.0')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles'
        ordering = ['role_category', 'role_name_en']
    
    def __str__(self):
        return f"{self.role_name_en} ({self.role_id})"


class RoleAssignment(models.Model):
    """
    Assignment of roles to users with scope.
    """
    
    SCOPE_TYPES = Role.SCOPE_TYPES
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('PendingApproval', 'Pending Approval'),
        ('Revoked', 'Revoked'),
    ]
    
    role_assignment_id = models.CharField(max_length=50, unique=True, primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='role_assignments'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='assignments'
    )
    
    # Scope
    scope_type = models.CharField(max_length=20, choices=SCOPE_TYPES, db_index=True)
    scope_ids = models.JSONField(default=list, help_text='List of admin unit IDs in scope')
    
    # Approval workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active', db_index=True)
    approval_required = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=20, default='Approved')
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_assignments'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Validity period
    effective_from = models.DateTimeField(default=timezone.now)
    effective_to = models.DateTimeField(null=True, blank=True)
    
    # Audit
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignments_made'
    )
    assigned_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'role_assignments'
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['role', 'scope_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.role.role_name_en} ({self.scope_type})"
    
    def is_active(self):
        """Check if assignment is currently active."""
        now = timezone.now()
        return (
            self.status == 'Active' and
            self.effective_from <= now and
            (self.effective_to is None or self.effective_to >= now)
        )


class DelegationPolicy(models.Model):
    """
    Defines which roles can assign which other roles.
    """
    
    delegation_policy_id = models.CharField(max_length=50, unique=True, primary_key=True)
    delegator_role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='delegation_policies'
    )
    allowed_roles_to_assign = models.JSONField(
        default=list,
        help_text='List of role IDs that can be assigned'
    )
    max_scope_level = models.CharField(
        max_length=100,
        help_text='Maximum scope level that can be assigned'
    )
    requires_approval_for_sensitive = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = 'delegation_policies'
    
    def __str__(self):
        return f"Delegation Policy for {self.delegator_role.role_name_en}"


class PasswordResetToken(models.Model):
    """
    Password reset token model for forgot password functionality.
    """
    token = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'used']),
            models.Index(fields=['user', 'used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Password reset token for {self.user.username} (expires: {self.expires_at})"
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        from django.utils import timezone
        return not self.used and timezone.now() < self.expires_at


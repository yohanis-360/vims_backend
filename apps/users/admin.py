"""
Django admin configuration for Users app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, RoleAssignment, DelegationPolicy


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'full_name', 'email', 'status', 'is_active', 'created_at']
    list_filter = ['status', 'is_active', 'mfa_enrolled']
    search_fields = ['username', 'full_name', 'email', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('user_id', 'username', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'email', 'phone', 'job_title')}),
        ('Status', {'fields': ('status', 'is_active', 'is_staff', 'is_superuser')}),
        ('Security', {'fields': ('mfa_enrolled', 'last_login_at', 'password_changed_at')}),
        ('Audit', {'fields': ('created_at', 'updated_at', 'created_by')}),
    )
    
    readonly_fields = ['user_id', 'created_at', 'updated_at', 'last_login_at']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['role_id', 'role_name_en', 'role_category', 'default_scope_type', 'enabled']
    list_filter = ['role_category', 'enabled', 'is_sensitive_role']
    search_fields = ['role_id', 'role_name_en']


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'scope_type', 'status', 'assigned_at']
    list_filter = ['status', 'scope_type']
    search_fields = ['user__username', 'role__role_name_en']
    raw_id_fields = ['user', 'approved_by', 'assigned_by']


@admin.register(DelegationPolicy)
class DelegationPolicyAdmin(admin.ModelAdmin):
    list_display = ['delegation_policy_id', 'delegator_role', 'enabled']
    list_filter = ['enabled']


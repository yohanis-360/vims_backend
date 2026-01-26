"""
Custom managers for User model with scope filtering.
"""
from django.db import models


class ScopedUserManager(models.Manager):
    """
    Manager for filtering users by scope.
    """
    
    def filter_by_scope(self, user_scope):
        """
        Filter users based on requesting user's scope.
        
        Args:
            user_scope: Dict with 'type' and 'ids' keys
        
        Returns:
            QuerySet of users within scope
        """
        queryset = self.get_queryset()
        
        if user_scope['type'] == 'National':
            # National scope can see all users
            return queryset
        
        if user_scope['type'] == 'Regional':
            # Regional users can see users in their region
            return queryset.filter(
                role_assignments__scope_ids__overlap=user_scope['ids'],
                role_assignments__status='Active'
            ).distinct()
        
        if user_scope['type'] == 'Center':
            # Center users can see users in their center
            return queryset.filter(
                role_assignments__scope_ids__overlap=user_scope['ids'],
                role_assignments__status='Active'
            ).distinct()
        
        return queryset.none()






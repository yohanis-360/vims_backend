"""
Setup script to create test inspector user
Run this with: docker-compose run --rm web1 python setup_test_user.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vims.settings')
django.setup()

from apps.users.models import User
from uuid import uuid4

def create_test_user():
    username = 'inspector001'
    
    # Check if user exists
    if User.objects.filter(username=username).exists():
        print(f"✓ User '{username}' already exists")
        user = User.objects.get(username=username)
        print(f"  User ID: {user.user_id}")
        print(f"  Status: {user.status}")
        return
    
    # Create user
    user = User.objects.create(
        user_id=f"USR-{str(uuid4())[:8].upper()}",
        username=username,
        full_name='Test Inspector',
        email='inspector@test.com',
        status='Active',
        is_active=True
    )
    user.set_password('test123')
    user.save()
    
    print(f"✓ User '{username}' created successfully")
    print(f"  User ID: {user.user_id}")
    print(f"  Password: test123")

if __name__ == '__main__':
    create_test_user()



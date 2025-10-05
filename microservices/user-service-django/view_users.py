"""
Quick script to view users in the database
Run this from the user-service-django directory
"""
import os
import django
import sys

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_service.settings')
django.setup()

from authentication.models import User

print("\n" + "="*80)
print("GYANSETU - REGISTERED USERS")
print("="*80 + "\n")

users = User.objects.all().order_by('-created_at')

if not users:
    print("No users found in database.")
else:
    print(f"Total Users: {users.count()}\n")
    print("-" * 80)
    
    for idx, user in enumerate(users, 1):
        print(f"\n{idx}. USER DETAILS:")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Username: {user.username}")
        print(f"   Verified: {'✅ Yes' if user.is_verified else '❌ No'}")
        print(f"   Active: {'✅ Yes' if user.is_active else '❌ No'}")
        print(f"   Profile Picture: {user.profile_picture if user.profile_picture else 'None'}")
        print(f"   Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)

print("\n")

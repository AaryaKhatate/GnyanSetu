"""
Emergency diagnostic - check what code Django is actually running
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_service.settings')
django.setup()

from authentication import views
import inspect

print("\n" + "="*70)
print("EMERGENCY DIAGNOSTIC - WHAT CODE IS DJANGO USING?")
print("="*70)

# Get the actual file path Django is loading
views_file = inspect.getfile(views)
print(f"\n✅ Django is loading views.py from:")
print(f"   {views_file}")

# Read the _create_user_session method
source = inspect.getsource(views.CustomTokenObtainPairView._create_user_session)

print(f"\n📄 Source code of _create_user_session method:")
print("-"*70)
print(source)
print("-"*70)

# Check for key phrases
if "Updated existing session" in source:
    print("\n❌ FOUND OLD CODE: 'Updated existing session'")
    print("   Django is using OLD SQLite code!")
elif "Created session in MongoDB" in source:
    print("\n✅ FOUND NEW CODE: 'Created session in MongoDB'")
    print("   Django is using NEW MongoDB code!")
elif "get_session_manager" in source:
    print("\n✅ FOUND: 'get_session_manager'")
    print("   Django has MongoDB code but maybe no logging?")
else:
    print("\n⚠️  UNKNOWN CODE - Neither old nor new patterns found")

print("\n" + "="*70 + "\n")

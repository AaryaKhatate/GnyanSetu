#!/usr/bin/env python3
"""
Test the MongoDB collection fix
"""
import sys
import os
sys.path.append(r'e:\Project\Gnyansetu_Updated_Architecture\microservices\lesson-service')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lesson_service.settings')
import django
django.setup()

from lessons.models import get_database_stats, check_database_connection

def test_mongodb_fix():
    """Test that the MongoDB collection fix works"""
    
    try:
        print("🔍 Testing MongoDB connection and stats...")
        
        # Test database connection
        is_connected = check_database_connection()
        print(f"   Database connected: {is_connected}")
        
        # Test database stats (this was causing the original error)
        stats = get_database_stats()
        print(f"   Stats retrieval: {'✅ Success' if stats.get('status') != 'error' else '❌ Failed'}")
        
        if stats.get('status') == 'error':
            print(f"   Error: {stats.get('error')}")
            return False
        else:
            print(f"   Status: {stats.get('status')}")
            print(f"   Database: {stats.get('database_name')}")
            print(f"   Collections: {stats.get('collections', {})}")
            print(f"   Total documents: {stats.get('total_documents', 0)}")
            
        print("\n🎉 MongoDB collection fix successful!")
        return True
        
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mongodb_fix()
    if success:
        print("\n🚀 The PDF upload should now work without the collection error!")
        print("   The 'Collection objects do not implement truth value testing' error is fixed.")
    else:
        print("\n⚠️  The fix needs more work.")
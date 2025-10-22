from pymongo import MongoClient
from datetime import datetime

db = MongoClient('localhost', 27017)['gnyansetu_users_django']
sessions = list(db['user_sessions'].find().sort('login_time', -1))

print("\n" + "="*60)
print("MONGODB SESSION CHECK")
print("="*60)
print(f"\n✅ Total sessions: {len(sessions)}\n")

if len(sessions) > 0:
    print("Most Recent Sessions:")
    print("-"*60)
    for s in sessions[:5]:
        login_time = s['login_time']
        time_ago = (datetime.utcnow() - login_time).total_seconds() / 60
        print(f"User: {s['user_email']}")
        print(f"Login: {login_time} ({int(time_ago)} minutes ago)")
        print(f"Active: {s['is_active']}")
        print(f"IP: {s['ip_address']}")
        print("-"*60)
    
    # Check for NEW session (within last 2 minutes)
    recent = [s for s in sessions if (datetime.utcnow() - s['login_time']).total_seconds() < 120]
    if recent:
        print(f"\n🎉 FOUND {len(recent)} NEW SESSION(S) FROM LAST 2 MINUTES!")
        print("✅ MongoDB session storage is WORKING!")
    else:
        print("\n⚠️ No sessions from last 2 minutes")
        print("❌ Django is still using OLD cached code")
else:
    print("❌ NO SESSIONS FOUND!")

print("\n" + "="*60 + "\n")

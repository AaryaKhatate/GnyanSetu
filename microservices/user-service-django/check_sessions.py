from pymongo import MongoClient

db = MongoClient('localhost', 27017)['gnyansetu_users_django']
sessions = list(db['user_sessions'].find())

print(f"\n✅ Total sessions in MongoDB: {len(sessions)}\n")

if len(sessions) > 0:
    print("Recent sessions:")
    for s in sessions[-5:]:
        print(f"  - User: {s['user_email']}, Active: {s['is_active']}, Login: {s['login_time']}")
    print("\n🎉 SUCCESS! Sessions are being saved to MongoDB!")
else:
    print("❌ NO SESSIONS FOUND - Still using old code!")

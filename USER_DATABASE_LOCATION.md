# 📊 User Data Storage Location - GnyanSetu

## 🎯 Quick Answer

Your users are stored in **TWO** places:

### 1. **SQLite Database** (Primary User Data)
- **File Location:** `d:\GnyanSetu\microservices\user-service-django\db.sqlite3`
- **Table Name:** `authentication_user`
- **What's Stored:** Email, username, password (hashed), basic info

### 2. **MongoDB** (Extended User Profiles)
- **Database:** `Gnyansetu_Users`
- **Collection:** `user_profiles`
- **What's Stored:** Learning preferences, study statistics, progress data

---

## 📋 Currently Registered Users (8 Total)

| Email | Username | Full Name | Created | Verified |
|-------|----------|-----------|---------|----------|
| chris@gmail.com | chris | Chris Gayle | Oct 4, 2025 | ❌ No |
| Dhruv@gmail.com | Dhruv | Dhruv Jurel | Oct 3, 2025 | ❌ No |
| kl@gmail.com | kl | KL Rahul | Oct 3, 2025 | ❌ No |
| rishab@gmail.com | rishab | Rishab Pant | Oct 3, 2025 | ❌ No |
| rohit@gmail.com | rohit | Rohit sharma | Oct 3, 2025 | ❌ No |
| virat@gmail.com | virat | virat kohli | Oct 3, 2025 | ❌ No |
| narad@gmail.com | narad | Narad muni | Oct 3, 2025 | ❌ No |
| john@gmail.com | john | John Dasly | Oct 3, 2025 | ❌ No |

---

## 🔍 How to View User Data

### **Option 1: SQLite Database Browser (Recommended)**

1. **Download DB Browser for SQLite:**
   - Website: https://sqlitebrowser.org/
   - Or use: https://sqliteviewer.app/ (online)

2. **Open Database:**
   - File: `d:\GnyanSetu\microservices\user-service-django\db.sqlite3`

3. **View Tables:**
   - `authentication_user` - Main user table
   - `authentication_userprofile` - User profiles
   - `authentication_usersession` - Login sessions

4. **See Your Data:**
   - Click "Browse Data" tab
   - Select table: `authentication_user`
   - You'll see all users with:
     - `id` (UUID)
     - `email`
     - `username`
     - `password` (hashed with Argon2)
     - `full_name`
     - `is_verified`
     - `created_at`
     - `updated_at`

### **Option 2: Django Admin Panel**

1. **Create a superuser first:**
   ```powershell
   cd d:\GnyanSetu\microservices\user-service-django
   python manage.py createsuperuser
   ```

2. **Access Admin:**
   - URL: http://localhost:8002/admin/
   - Login with superuser credentials
   - Click "Users" to see all registered users

### **Option 3: MongoDB Compass (For Extended Profiles)**

1. **Open MongoDB Compass**
2. **Connect to:** `mongodb://localhost:27017`
3. **Database:** `Gnyansetu_Users`
4. **Collections:**
   - `user_profiles` - Extended user profile data

### **Option 4: Django Shell (Command Line)**

```powershell
cd d:\GnyanSetu\microservices\user-service-django
python manage.py shell
```

Then in the shell:
```python
from authentication.models import User

# See all users
User.objects.all()

# Find specific user by email
user = User.objects.get(email='kl@gmail.com')
print(f"Username: {user.username}")
print(f"Email: {user.email}")
print(f"Full Name: {user.full_name}")
print(f"Verified: {user.is_verified}")

# Count total users
User.objects.count()
```

### **Option 5: SQL Query (Direct)**

```powershell
cd d:\GnyanSetu\microservices\user-service-django
sqlite3 db.sqlite3
```

Then run SQL:
```sql
-- See all users
SELECT email, username, full_name, is_verified, created_at 
FROM authentication_user;

-- Find specific user
SELECT * FROM authentication_user WHERE email = 'kl@gmail.com';

-- Count users
SELECT COUNT(*) FROM authentication_user;

-- Exit
.quit
```

---

## 📂 Complete File Structure

```
d:\GnyanSetu\microservices\user-service-django\
├── db.sqlite3                    ← YOUR USERS ARE HERE!
├── authentication/
│   └── models.py                 ← User model definition
├── user_service/
│   └── settings.py              ← Database configuration
└── manage.py
```

---

## 🗄️ Database Schema

### **SQLite Table: `authentication_user`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key (unique ID) |
| `password` | VARCHAR(128) | Hashed password (Argon2) |
| `last_login` | DATETIME | Last login timestamp |
| `is_superuser` | BOOLEAN | Admin status |
| `username` | VARCHAR(150) | Unique username |
| `email` | VARCHAR(254) | Unique email |
| `full_name` | VARCHAR(255) | User's full name |
| `phone_number` | VARCHAR(17) | Phone (optional) |
| `date_of_birth` | DATE | Birthday (optional) |
| `is_verified` | BOOLEAN | Email verified? |
| `is_active` | BOOLEAN | Account active? |
| `is_staff` | BOOLEAN | Staff status |
| `created_at` | DATETIME | Account creation time |
| `updated_at` | DATETIME | Last update time |

---

## 🎯 Quick Access Commands

### View all users:
```powershell
cd d:\GnyanSetu\microservices\user-service-django
python manage.py shell -c "from authentication.models import User; [print(f'{u.email} - {u.full_name}') for u in User.objects.all()]"
```

### Find your latest user:
```powershell
python manage.py shell -c "from authentication.models import User; u = User.objects.latest('created_at'); print(f'Latest: {u.email} ({u.full_name})')"
```

### Check user count:
```powershell
python manage.py shell -c "from authentication.models import User; print(f'Total Users: {User.objects.count()}')"
```

---

## 🔐 Security Note

**Passwords are hashed using Argon2** - the most secure hashing algorithm. You'll see something like:
```
argon2$argon2id$v=19$m=102400,t=2,p=8$...
```

This is **secure** and **cannot be reversed** to see the plain password.

---

## ✅ Summary

**Your user data is in:**
- **Primary Location:** `d:\GnyanSetu\microservices\user-service-django\db.sqlite3`
- **Table:** `authentication_user`
- **Total Users:** 8 (as of now)
- **Latest User:** chris@gmail.com (Chris Gayle)

**Best way to view:**
1. Download **DB Browser for SQLite**
2. Open `db.sqlite3` file
3. Browse the `authentication_user` table

That's it! 🎉

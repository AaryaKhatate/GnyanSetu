# Password Error Messages - Concise Version

## ✅ All Error Messages (One Line Each)

| Validation Rule | Error Message |
|----------------|---------------|
| **Too Short** | `Password must be at least 8 characters.` |
| **No Number** | `Password must include at least one number.` |
| **No Uppercase** | `Password must include at least one uppercase letter.` |
| **No Special Char** | `Password must include a special character (!@#$%^&* etc).` |
| **Too Common** | `Password must include letters, numbers, and special characters.` |
| **Only Numbers** | `Password must include letters and special characters.` |
| **Too Similar** | `Password too similar to your personal info.` |

---

## 🧪 Detailed Test Examples

### ❌ Password: `12345678` (no letters, no special chars)
```
Error: "Password must include letters, numbers, and special characters. 
Password must include letters and special characters. 
Password must include a special character (!@#$%^&* etc)."
```

### ❌ Password: `password123` (no uppercase, no special character)
```
Error: "Password must include at least one uppercase letter. 
Password must include a special character (!@#$%^&* etc)."
```

### ❌ Password: `Password123` (no special character)
```
Error: "Password must include a special character (!@#$%^&* etc)."
```

### ❌ Password: `Password!@#` (no number)
```
Error: "Password must include at least one number."
```

### ❌ Password: `password!@#1` (no uppercase)
```
Error: "Password must include at least one uppercase letter."
```

### ❌ Password: `PASSWORDTEST` (no number, no special char)
```
Error: "Password must include at least one number. 
Password must include a special character (!@#$%^&* etc)."
```

### ❌ Password: `abc` (too short, no uppercase, no number, no special char)
```
Error: "Password must be at least 8 characters. 
Password must include at least one number. 
Password must include at least one uppercase letter. 
Password must include a special character (!@#$%^&* etc)."
```

### ✅ Password: `TestUser123!` (all requirements met)
```
Success! ✓
```

---

## 📋 Quick Validation Checklist

Every password is checked for:
- ✅ **Length**: At least 8 characters
- ✅ **Uppercase**: Must have at least one uppercase letter (A-Z)
- ✅ **Number**: Must have at least one digit (0-9)
- ✅ **Special Char**: Must have at least one (!@#$%^&* etc)
- ✅ **Not Common**: Can't be a common password
- ✅ **Not Only Numbers**: Must have letters too
- ✅ **Not Too Similar**: Can't be like username/email

---

## 🎯 Password Requirements Summary

**Valid password needs ALL of these:**
1. 8+ characters
2. At least 1 uppercase letter (A-Z)
3. At least 1 number (0-9)
4. At least 1 special character (!@#$%^&* etc)
5. Not entirely numeric
6. Not too common
7. Not similar to your info

**Quick examples of VALID passwords:**
- `TestUser123!` ✅
- `MyPass2024@` ✅
- `Secure99#` ✅
- `Hello2024$` ✅
- `Welcome@123` ✅

**Quick examples of INVALID passwords:**
- `password123!` ❌ (no uppercase)
- `Password!@#` ❌ (no number)
- `Password123` ❌ (no special char)
- `PASSWORD123!` ❌ (no lowercase - will fail similarity check)
- `12345678` ❌ (only numbers)
- `pass` ❌ (too short)

---

## 🚀 To Apply Changes

Restart your Django server:
```powershell
# Press Ctrl+C to stop
# Then restart:
python manage.py runserver 0.0.0.0:8002
```

All error messages are now **helpful and actionable**! 🎉

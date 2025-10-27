# GnyanSetu - Quick Reference Guide
## 🚀 Start Here

### 1. Start the Platform (ONE COMMAND)
```bash
cd E:\Project\GnyanSetu\microservices
.\start_project.bat
```

### 2. Access Dashboard
```
http://localhost:3001
```

### 3. Upload PDF & Generate Lesson
- Click upload box
- Select PDF file  
- Wait for processing

### 4. Enter Teaching Mode
```
http://localhost:3001/teaching
```
OR
```
http://localhost:3001/teaching/<lesson_id>
```

---

## ✅ ALL FIXES APPLIED

| # | Fix | Status |
|---|-----|--------|
| 1 | react-router-dom installed | ✅ Done |
| 2 | axios installed | ✅ Done |
| 3 | use-image installed | ✅ Done |
| 4 | TeachingSessionSimple.jsx created | ✅ Done |
| 5 | TeachingSession.css created | ✅ Done |
| 6 | ttsController.js created | ✅ Done |
| 7 | App.jsx routing added | ✅ Done |
| 8 | CORS verified (already working) | ✅ Done |
| 9 | Build tested (successful) | ✅ Done |

---

## 🎯 Testing Checklist

### Before Testing
- [ ] All services running (check `start_project.bat` output)
- [ ] MongoDB running
- [ ] Browser console open (F12)

### Test Steps
1. [ ] Upload PDF successfully
2. [ ] See lesson generated message
3. [ ] Navigate to `http://localhost:3001/teaching`
4. [ ] See "Start Lesson" button
5. [ ] Click Start - TTS begins
6. [ ] Whiteboard shows visuals
7. [ ] Auto-advances to next step
8. [ ] Progress bar updates
9. [ ] "Next" button works
10. [ ] "Repeat" button works
11. [ ] "Pause" button works
12. [ ] Complete all steps

---

## 🔧 Key Files Modified

```
Dashboard/src/App.jsx                     [UPDATED - Router added]
Dashboard/src/components/TeachingSessionSimple.jsx  [CREATED]
Dashboard/src/components/TeachingSession.css        [CREATED]
Dashboard/src/utils/ttsController.js                [CREATED]
Dashboard/package.json                    [UPDATED - deps added]
```

---

## 🌐 Service Ports

| Service | Port | URL |
|---------|------|-----|
| Landing Page | 3000 | http://localhost:3000 |
| **Dashboard** | **3001** | **http://localhost:3001** |
| API Gateway | 8000 | http://localhost:8000 |
| User Service | 8002 | http://localhost:8002 |
| Lesson Service | 8003 | http://localhost:8003 |
| Teaching Service | 8004 | http://localhost:8004 |
| Quiz Notes | 8005 | http://localhost:8005 |
| **Visualization** | **8006** | **http://localhost:8006** |

---

## 🐛 Common Issues & Quick Fixes

### Issue: "Cannot find module"
```bash
cd E:\Project\GnyanSetu\virtual_teacher_project\UI\Dashboard\Dashboard
npm install
```

### Issue: Services not running
```bash
cd E:\Project\GnyanSetu\microservices
.\start_project.bat
```

### Issue: MongoDB error
- Install MongoDB: https://www.mongodb.com/try/download/community
- Start MongoDB service

### Issue: CORS error
- Check visualization service is running
- Restart visualization service if needed

### Issue: TTS not working
- Use Chrome browser (best Web Speech API support)
- Check system volume
- Allow microphone permissions if prompted

---

## 📞 Support Commands

### Verify All Fixes
```powershell
cd E:\Project\GnyanSetu
.\verify_fixes.ps1
```

### Check Service Health
```bash
curl http://localhost:8006/health
curl http://localhost:8003/health
```

### Check Installed Dependencies
```bash
cd E:\Project\GnyanSetu\virtual_teacher_project\UI\Dashboard\Dashboard
npm list react-router-dom axios use-image
```

### Rebuild Dashboard
```bash
cd E:\Project\GnyanSetu\virtual_teacher_project\UI\Dashboard\Dashboard
npm run build
```

---

## 🎓 How It Works

```
1. PDF Upload
   ↓
2. Lesson Service generates lesson
   ↓
3. Visualization Service creates whiteboard commands
   ↓
4. Data saved to sessionStorage
   ↓
5. Navigate to /teaching
   ↓
6. TeachingSessionSimple loads data
   ↓
7. [Whiteboard rendering + TTS narration]
   ↓
8. Step-by-step learning!
```

---

## 🎉 Success Indicators

When everything works:
- ✅ No errors in browser console
- ✅ Services show "✅ healthy" in terminal
- ✅ Upload shows success message
- ✅ /teaching page loads without 404
- ✅ Canvas displays whiteboard
- ✅ TTS voice plays clearly
- ✅ Auto-advance works
- ✅ Controls respond to clicks

---

## 📖 Full Documentation

See: `COMPLETE_FIX_DOCUMENTATION.md` for:
- Detailed architecture
- All fixes explained
- Troubleshooting guide
- Developer notes
- Future enhancements

---

**Last Updated**: October 25, 2025  
**Status**: ✅ All fixes applied, ready for testing!

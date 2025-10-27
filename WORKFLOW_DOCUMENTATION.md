# GNYANSETU - COMPLETE SYSTEM WORKFLOW DOCUMENTATION

## ARCHITECTURE OVERVIEW

```
Frontend (React)          API Gateway          Microservices
   Port 3000/3001    →    Port 8000      →    Ports 8002-8006
        │                     │                      │
        │                     │         ┌────────────┼────────────┐
        │                     │         │            │            │
        └─────────────────────┴─────────┤            │            │
                                        ▼            ▼            ▼
                                    User-8002   Lesson-8003  Teaching-8004
                                        │            │            │
                                        │            │            │
                                        ▼            ▼            ▼
                                    Quiz-8005   Viz-8006    MongoDB
```

---

## WORKFLOW 1: USER REGISTRATION & LOGIN

### 1.1 USER REGISTRATION FLOW

```
┌─────────────┐    POST     ┌─────────────┐   Forward   ┌─────────────┐
│  Frontend   │────────────→│ API Gateway │────────────→│ User Service│
│ Port 3000/1 │             │  Port 8000  │             │  Port 8002  │
└─────────────┘             └─────────────┘             └─────────────┘
      │                                                         │
      │ User clicks "Sign Up"                                  │
      │ Enters: name, email, password                          │
      │                                                         │
      └────────────────────────────────────────────────────────┘
                                                                │
                                                                ▼
                                                    ┌───────────────────────┐
                                                    │ VALIDATION            │
                                                    │ - Email format check  │
                                                    │ - Password length ≥6  │
                                                    │ - Required fields     │
                                                    └───────────────────────┘
                                                                │
                                                                ▼
                                                    ┌───────────────────────┐
                                                    │ DATABASE CHECK        │
                                                    │ MongoDB Query:        │
                                                    │ users.find_one(       │
                                                    │   {email: email}      │
                                                    │ )                     │
                                                    └───────────────────────┘
                                                                │
                                                    ┌───────────┴───────────┐
                                                    │                       │
                                            EXISTS ▼                  NOT EXISTS ▼
                                        Return 409 Error          Continue Registration
                                        "Already registered"               │
                                                                           ▼
                                                            ┌──────────────────────────┐
                                                            │ PASSWORD HASHING         │
                                                            │ bcrypt.hashpw(           │
                                                            │   password, salt         │
                                                            │ )                        │
                                                            │ Returns: password_hash   │
                                                            └──────────────────────────┘
                                                                           │
                                                                           ▼
                                                            ┌──────────────────────────┐
                                                            │ CREATE USER DOCUMENT     │
                                                            │ {                        │
                                                            │   name: "...",          │
                                                            │   email: "...",         │
                                                            │   password_hash: "...", │
                                                            │   role: "student",      │
                                                            │   created_at: UTC now,  │
                                                            │   is_active: true,      │
                                                            │   email_verified: false,│
                                                            │   profile: {}           │
                                                            │ }                        │
                                                            └──────────────────────────┘
                                                                           │
                                                                           ▼
                                                            ┌──────────────────────────┐
                                                            │ INSERT INTO MONGODB      │
                                                            │ Collection: users        │
                                                            │ Database: Gnyansetu_Users│
                                                            │ Returns: _id (ObjectId)  │
                                                            └──────────────────────────┘
                                                                           │
                                                                           ▼
                                                            ┌──────────────────────────┐
                                                            │ GENERATE JWT TOKEN       │
                                                            │ Payload: {               │
                                                            │   user_id: str(_id),    │
                                                            │   email: email,         │
                                                            │   name: name,           │
                                                            │   role: "student",      │
                                                            │   exp: UTC + 24h,       │
                                                            │   iat: UTC now          │
                                                            │ }                        │
                                                            │ Algorithm: HS256         │
                                                            │ Secret: JWT_SECRET       │
                                                            └──────────────────────────┘
                                                                           │
                                                                           ▼
                                                            ┌──────────────────────────┐
                                                            │ PUBLISH EVENT (RabbitMQ) │
                                                            │ Exchange: user_events    │
                                                            │ Routing: user.registered │
                                                            │ Data: {user_id, email}  │
                                                            └──────────────────────────┘
                                                                           │
                                                                           ▼
                                                            ┌──────────────────────────┐
                                                            │ RETURN RESPONSE 201      │
                                                            │ {                        │
                                                            │   success: true,         │
                                                            │   user: {...},           │
                                                            │   token: "JWT..."        │
                                                            │ }                        │
                                                            └──────────────────────────┘
```

**File**: `microservices/user-service/app.py`
- **Function**: `signup()` (Line 278)
- **Endpoint**: `POST /api/auth/signup/`
- **Database**: MongoDB `Gnyansetu_Users.users`

---

### 1.2 USER LOGIN FLOW

```
Frontend → API Gateway → User Service
                            │
                            ▼
                ┌──────────────────────────┐
                │ EXTRACT CREDENTIALS      │
                │ email = request.email    │
                │ password = request.pwd   │
                └──────────────────────────┘
                            │
                            ▼
                ┌──────────────────────────┐
                │ FIND USER IN DATABASE    │
                │ users.find_one(          │
                │   {email: email}         │
                │ )                        │
                └──────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        NOT FOUND ▼               FOUND ▼
        Return 401              Continue
        "Invalid credentials"        │
                                     ▼
                        ┌──────────────────────────┐
                        │ VERIFY PASSWORD          │
                        │ bcrypt.checkpw(          │
                        │   input_password,        │
                        │   stored_hash            │
                        │ )                        │
                        └──────────────────────────┘
                                     │
                        ┌────────────┴────────────┐
                        │                         │
                  INVALID ▼                  VALID ▼
                Return 401              Check if active
                "Invalid creds"              │
                                             ▼
                                ┌──────────────────────────┐
                                │ CHECK is_active FLAG     │
                                │ if not active:           │
                                │   return 401 error       │
                                └──────────────────────────┘
                                             │
                                             ▼
                                ┌──────────────────────────┐
                                │ UPDATE LAST LOGIN        │
                                │ users.update_one(        │
                                │   {_id: user_id},        │
                                │   {last_login: UTC now}  │
                                │ )                        │
                                └──────────────────────────┘
                                             │
                                             ▼
                                ┌──────────────────────────┐
                                │ GENERATE JWT TOKEN       │
                                │ (Same process as signup) │
                                └──────────────────────────┘
                                             │
                                             ▼
                                ┌──────────────────────────┐
                                │ CREATE SESSION RECORD    │
                                │ sessions.insert({        │
                                │   user_id: user_id,      │
                                │   token: token,          │
                                │   created_at: UTC now,   │
                                │   expires_at: UTC + 24h  │
                                │ })                       │
                                └──────────────────────────┘
                                             │
                                             ▼
                                ┌──────────────────────────┐
                                │ PUBLISH LOGIN EVENT      │
                                │ RabbitMQ: user.login     │
                                └──────────────────────────┘
                                             │
                                             ▼
                                ┌──────────────────────────┐
                                │ RETURN RESPONSE 200      │
                                │ {                        │
                                │   success: true,         │
                                │   user: {...},           │
                                │   token: "JWT...",       │
                                │   expires_in: 86400      │
                                │ }                        │
                                └──────────────────────────┘
```

**File**: `microservices/user-service/app.py`
- **Function**: `login()` (Line 378)
- **Endpoint**: `POST /api/auth/login/`
- **Database Collections**: 
  - `Gnyansetu_Users.users` (user lookup)
  - `Gnyansetu_Users.sessions` (session tracking)

---

## WORKFLOW 2: PDF UPLOAD & LESSON GENERATION

### 2.1 PDF UPLOAD & PROCESSING FLOW

```
┌──────────┐         ┌─────────┐         ┌──────────────┐
│ Frontend │────────→│ Gateway │────────→│ Lesson Service│
│  Upload  │  POST   │  :8000  │ Forward │    :8003     │
│   PDF    │         └─────────┘         └──────────────┘
└──────────┘                                     │
                                                 ▼
                                    ┌────────────────────────────┐
                                    │ ENDPOINT RECEIVES REQUEST  │
                                    │ POST /api/generate-lesson/ │
                                    │                            │
                                    │ Files: pdf_file            │
                                    │ Data: user_id, lesson_type │
                                    └────────────────────────────┘
                                                 │
                                                 ▼
                                    ┌────────────────────────────┐
                                    │ VALIDATE PDF FILE          │
                                    │ - Check file exists        │
                                    │ - Check file type          │
                                    │ - Max size: 50MB           │
                                    │ - Read header bytes        │
                                    └────────────────────────────┘
                                                 │
                                                 ▼
                                    ┌────────────────────────────┐
                                    │ PROCESS PDF                │
                                    │ pdf_processor.process_pdf()│
                                    │                            │
                                    │ Uses: PyPDF2 + Pillow      │
                                    └────────────────────────────┘
                                                 │
                                    ┌────────────┴────────────┐
                                    │                         │
                                    ▼                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │ EXTRACT TEXT    │     │ EXTRACT IMAGES  │
                        │ For each page:  │     │ For each page:  │
                        │ - Read text     │     │ - Find images   │
                        │ - Clean format  │     │ - Convert format│
                        │ - Store content │     │ - OCR text      │
                        └─────────────────┘     └─────────────────┘
                                    │                         │
                                    └────────────┬────────────┘
                                                 ▼
                                    ┌────────────────────────────┐
                                    │ COMBINE RESULTS            │
                                    │ {                          │
                                    │   text_content: "...",     │
                                    │   images_data: [...],      │
                                    │   metadata: {              │
                                    │     pages: 10,             │
                                    │     images: 5,             │
                                    │     text_length: 5000      │
                                    │   }                        │
                                    │ }                          │
                                    └────────────────────────────┘
                                                 │
                                                 ▼
                                    ┌────────────────────────────┐
                                    │ STORE PDF DATA IN MONGODB  │
                                    │ Collection: pdf_data       │
                                    │ Database: Gnyansetu_Lessons│
                                    │                            │
                                    │ PDFDataModel.create({      │
                                    │   user_id: user_id,        │
                                    │   filename: "file.pdf",    │
                                    │   text_content: "...",     │
                                    │   images_data: [...],      │
                                    │   metadata: {...}          │
                                    │ })                         │
                                    │                            │
                                    │ Returns: pdf_id (ObjectId) │
                                    └────────────────────────────┘
```

**File**: `microservices/lesson-service/lessons/views.py`
- **Function**: `process_pdf_and_generate_lesson()` (Line 107)
- **Endpoint**: `POST /api/generate-lesson/`

**PDF Processor**: `microservices/lesson-service/lessons/pdf_processor.py`
- **Function**: `process_pdf()`
- **Libraries**: PyPDF2 (text), Pillow (images), pytesseract (OCR)

---

### 2.2 AI LESSON GENERATION FLOW

```
[After PDF Processing]
         │
         ▼
┌────────────────────────────┐
│ PREPARE CONTENT FOR AI     │
│ - pdf_text = extracted     │
│ - images_ocr = OCR text    │
│ - lesson_type = "inter..."│
│ - user_context = {user_id} │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ CALL LESSON GENERATOR      │
│ lesson_generator.generate_ │
│ lesson(pdf_text, ocr, type)│
└────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ CONSTRUCT GEMINI AI PROMPT                             │
│                                                        │
│ System Prompt:                                         │
│ "You are an expert educational content creator..."     │
│                                                        │
│ User Prompt Template:                                  │
│ "Create an interactive lesson from this content:       │
│  [PDF_TEXT]                                            │
│  [OCR_TEXT]                                            │
│                                                        │
│  Generate:                                             │
│  1. Engaging title                                     │
│  2. Clear introduction                                 │
│  3. Structured sections with explanations              │
│  4. Visual descriptions for animations                 │
│  5. Practice exercises                                 │
│  6. Summary                                            │
│                                                        │
│  Format as Markdown with visualization notes"          │
└────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ CONFIGURE GEMINI MODEL     │
│                            │
│ genai.configure(           │
│   api_key=GEMINI_API_KEY   │
│ )                          │
│                            │
│ model = GenerativeModel(   │
│   'gemini-2.0-flash-exp'   │
│ )                          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ CALL GEMINI API            │
│                            │
│ response = model.generate_ │
│ content(                   │
│   prompt,                  │
│   generation_config={      │
│     temperature: 0.7,      │
│     max_output_tokens:8000,│
│     top_p: 0.9,            │
│     top_k: 40              │
│   }                        │
│ )                          │
│                            │
│ ⏱️ Takes: 3-10 seconds     │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ PARSE AI RESPONSE          │
│ - Extract text content     │
│ - Clean markdown           │
│ - Extract viz notes        │
│ - Format sections          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ EXTRACT VISUALIZATION JSON │
│                            │
│ visualization_extractor.   │
│ extract_from_content(      │
│   lesson_content           │
│ )                          │
│                            │
│ Parses:                    │
│ - Scene descriptions       │
│ - Shape definitions        │
│ - Animation sequences      │
│ - Audio narration          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ STORE LESSON IN MONGODB    │
│ Collection: lessons        │
│                            │
│ LessonModel.create({       │
│   user_id: user_id,        │
│   pdf_id: pdf_id,          │
│   lesson_title: "...",     │
│   lesson_content: "...",   │
│   visualization_json: {},  │
│   quiz_data: {},  ← EMPTY  │
│   notes_data: {}, ← EMPTY  │
│   quiz_notes_status:       │
│     "generating",          │
│   metadata: {...}          │
│ })                         │
│                            │
│ Returns: lesson_id         │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ CREATE HISTORY ENTRY       │
│ Collection: user_histories │
│                            │
│ UserHistoryModel.create({  │
│   user_id: user_id,        │
│   pdf_id: pdf_id,          │
│   lesson_id: lesson_id,    │
│   action: "generated",     │
│   timestamp: UTC now       │
│ })                         │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ RETURN RESPONSE TO CLIENT  │
│                            │
│ {                          │
│   success: true,           │
│   pdf_id: "...",           │
│   lesson_id: "...",        │
│   lesson: {                │
│     title: "...",          │
│     content: "..." (15KB)  │
│   },                       │
│   quiz_notes_status:       │
│     "generating",          │
│   message: "Lesson ready.  │
│     Quiz/notes generating  │
│     in background"         │
│ }                          │
└────────────────────────────┘
```

**File**: `microservices/lesson-service/lessons/lesson_generator.py`
- **Class**: `LessonGenerator`
- **Function**: `generate_lesson()` (Line 100)
- **AI Model**: Gemini 2.0 Flash Experimental
- **Database**: MongoDB `Gnyansetu_Lessons.lessons`

---

## WORKFLOW 3: ASYNC QUIZ & NOTES GENERATION

### 3.1 BACKGROUND THREAD INITIALIZATION

```
[After Main Lesson Generated]
         │
         ▼
┌────────────────────────────┐
│ START BACKGROUND THREAD    │
│                            │
│ thread = Thread(           │
│   target=generate_quiz_    │
│          and_notes_async,  │
│   args=(                   │
│     lesson_id,             │
│     lesson_content,        │
│     lesson_title           │
│   ),                       │
│   daemon=True              │
│ )                          │
│ thread.start()             │
│                            │
│ ✅ Main request returns    │
│    immediately             │
└────────────────────────────┘
         │
         ▼ (New Thread)
┌────────────────────────────┐
│ ASYNC FUNCTION STARTS      │
│ generate_quiz_and_notes_   │
│ async()                    │
│                            │
│ Runs independently of      │
│ main request thread        │
└────────────────────────────┘
```

**File**: `microservices/lesson-service/lessons/views.py`
- **Function**: `generate_quiz_and_notes_async()` (Line 25)
- **Thread**: Daemon background thread

---

### 3.2 QUIZ GENERATION FLOW

```
[Background Thread]
         │
         ▼
┌────────────────────────────┐
│ CALL QUIZ GENERATOR        │
│                            │
│ quiz_data = lesson_gen.    │
│ generate_quiz_data(        │
│   lesson_content=content,  │
│   lesson_title=title       │
│ )                          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ CONSTRUCT QUIZ PROMPT FOR GEMINI                       │
│                                                        │
│ "Based on this lesson content, generate a quiz:        │
│  [LESSON_CONTENT]                                      │
│                                                        │
│  Create 5-10 multiple choice questions that:          │
│  - Test understanding of key concepts                  │
│  - Have 4 options (A, B, C, D)                         │
│  - Include correct answer                              │
│  - Provide explanation for correct answer              │
│                                                        │
│  Return ONLY valid JSON in this exact format:          │
│  {                                                     │
│    'title': 'Quiz: [TOPIC]',                          │
│    'questions': [                                      │
│      {                                                 │
│        'question': 'Question text?',                   │
│        'options': [                                    │
│          {'key': 'A', 'text': '...'},                 │
│          {'key': 'B', 'text': '...'},                 │
│          {'key': 'C', 'text': '...'},                 │
│          {'key': 'D', 'text': '...'}                  │
│        ],                                              │
│        'correct_answer': 'A',                          │
│        'explanation': 'Why A is correct...'            │
│      }                                                 │
│    ]                                                   │
│  }                                                     │
│                                                        │
│  NO markdown, NO code blocks, ONLY JSON"               │
└────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ CALL GEMINI AI             │
│                            │
│ response = model.generate_ │
│ content(                   │
│   quiz_prompt,             │
│   generation_config={      │
│     temperature: 0.2,      │
│     max_output_tokens:3000,│
│     response_mime_type:    │
│       "application/json"   │
│   }                        │
│ )                          │
│                            │
│ ⏱️ Takes: 5-15 seconds     │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ PARSE & CLEAN RESPONSE     │
│                            │
│ 1. Extract text            │
│ 2. Remove markdown blocks  │
│ 3. Remove ```json          │
│ 4. Trim whitespace         │
│ 5. Find first {            │
│ 6. Find last }             │
│ 7. Extract JSON substring  │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ FIX JSON ERRORS            │
│ _fix_json_errors()         │
│                            │
│ - Fix trailing commas      │
│ - Escape quotes            │
│ - Fix newlines             │
│ - Balance brackets         │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ TRY PARSE JSON             │
│                            │
│ try:                       │
│   quiz_data=json.loads(    │
│     quiz_text              │
│   )                        │
│ except JSONDecodeError:    │
│   → Aggressive fix         │
│ except Exception:          │
│   → Fallback quiz          │
└────────────────────────────┘
         │
    ┌────┴────┐
    │         │
SUCCESS ▼    FAIL ▼
    │         │
    │    ┌────────────────────────────┐
    │    │ RETURN FALLBACK QUIZ       │
    │    │ {                          │
    │    │   title: "Quiz: [Topic]",  │
    │    │   questions: [             │
    │    │     {                      │
    │    │       question: "What is   │
    │    │         the main topic?",  │
    │    │       options: [A,B,C,D],  │
    │    │       correct: "A",        │
    │    │       explanation: "..."   │
    │    │     }                      │
    │    │   ]                        │
    │    │ }                          │
    │    └────────────────────────────┘
    │         │
    └────┬────┘
         ▼
┌────────────────────────────┐
│ VALIDATE STRUCTURE         │
│                            │
│ if 'questions' not in data:│
│   raise ValueError         │
│                            │
│ for q in questions:        │
│   validate question        │
│   validate options (4)     │
│   validate correct answer  │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ RETURN QUIZ DATA           │
│ To async function          │
└────────────────────────────┘
```

**File**: `microservices/lesson-service/lessons/lesson_generator.py`
- **Function**: `generate_quiz_data()` (Line 1330)
- **Fallback**: `_get_fallback_quiz()` (Line 1732)

---

### 3.3 NOTES GENERATION FLOW

```
[Background Thread - After Quiz]
         │
         ▼
┌────────────────────────────┐
│ CALL NOTES GENERATOR       │
│                            │
│ notes_data = lesson_gen.   │
│ generate_notes_data(       │
│   lesson_content=content,  │
│   lesson_title=title       │
│ )                          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ CONSTRUCT NOTES PROMPT FOR GEMINI                      │
│                                                        │
│ "Create comprehensive study notes from this lesson:    │
│  [LESSON_CONTENT]                                      │
│                                                        │
│  Generate structured notes with:                       │
│  1. Brief summary of entire lesson                     │
│  2. Key sections with important points                 │
│  3. Important terms and definitions                    │
│                                                        │
│  Return ONLY valid JSON in this format:                │
│  {                                                     │
│    'title': 'Notes: [TOPIC]',                         │
│    'summary': 'Brief overview...',                     │
│    'sections': [                                       │
│      {                                                 │
│        'heading': 'Section Title',                     │
│        'key_points': [                                 │
│          'Point 1',                                    │
│          'Point 2',                                    │
│          ...                                           │
│        ]                                               │
│      }                                                 │
│    ],                                                  │
│    'key_terms': [                                      │
│      {                                                 │
│        'term': 'Term name',                            │
│        'definition': 'Clear definition'                │
│      }                                                 │
│    ]                                                   │
│  }                                                     │
│                                                        │
│  NO markdown, NO code blocks, ONLY JSON"               │
└────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ CALL GEMINI AI             │
│ (Same process as quiz)     │
│                            │
│ ⏱️ Takes: 5-15 seconds     │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ PARSE & VALIDATE           │
│ (Same JSON parsing as quiz)│
└────────────────────────────┘
         │
    ┌────┴────┐
    │         │
SUCCESS ▼    FAIL ▼
    │         │
    │    ┌────────────────────────────┐
    │    │ RETURN FALLBACK NOTES      │
    │    │ {                          │
    │    │   title: "Notes: [Topic]", │
    │    │   summary: "Review...",    │
    │    │   sections: [              │
    │    │     {                      │
    │    │       heading: "Main...",  │
    │    │       key_points: [...]    │
    │    │     }                      │
    │    │   ],                       │
    │    │   key_terms: []            │
    │    │ }                          │
    │    └────────────────────────────┘
    │         │
    └────┬────┘
         ▼
┌────────────────────────────┐
│ RETURN NOTES DATA          │
│ To async function          │
└────────────────────────────┘
```

**File**: `microservices/lesson-service/lessons/lesson_generator.py`
- **Function**: `generate_notes_data()` (Line 1517)
- **Fallback**: `_get_fallback_notes()` (Line 1503)

---

### 3.4 DATABASE UPDATE FLOW

```
[After Both Quiz & Notes Generated]
         │
         ▼
┌────────────────────────────┐
│ UPDATE LESSON IN MONGODB   │
│                            │
│ lessons.update_one(        │
│   {'_id': ObjectId(        │
│     lesson_id              │
│   )},                      │
│   {                        │
│     '$set': {              │
│       'quiz_data': {       │
│         title: "...",      │
│         questions: [...]   │
│       },                   │
│       'notes_data': {      │
│         title: "...",      │
│         summary: "...",    │
│         sections: [...]    │
│       },                   │
│       'quiz_notes_         │
│         generated_at':     │
│         UTC now,           │
│       'quiz_notes_status': │
│         'completed'        │
│     }                      │
│   }                        │
│ )                          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ LOG SUCCESS                │
│ print("✅ Quiz & Notes     │
│   generated successfully") │
│ print(f"Questions: {count}")│
│ print(f"Sections: {count}") │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ THREAD COMPLETES           │
│ Background task done       │
└────────────────────────────┘
```

**On Error:**
```
┌────────────────────────────┐
│ CATCH EXCEPTION            │
│                            │
│ except Exception as e:     │
│   logger.error(e)          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ UPDATE STATUS TO FAILED    │
│                            │
│ lessons.update_one(        │
│   {'_id': lesson_id},      │
│   {                        │
│     '$set': {              │
│       'quiz_notes_status': │
│         'failed',          │
│       'quiz_notes_error':  │
│         str(e)             │
│     }                      │
│   }                        │
│ )                          │
└────────────────────────────┘
```

**File**: `microservices/lesson-service/lessons/views.py`
- **Function**: `generate_quiz_and_notes_async()` (Line 25-89)

---

## WORKFLOW 4: VISUALIZATION GENERATION

### 4.1 VISUALIZATION PROCESSING FLOW

```
[Lesson Service has visualization_json]
         │
         ▼
┌────────────────────────────┐
│ FRONTEND REQUESTS VIZ      │
│                            │
│ POST /api/visualizations/  │
│      process               │
│                            │
│ Body: {                    │
│   lesson_id: "...",        │
│   topic: "...",            │
│   scenes: [...]            │
│ }                          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ VISUALIZATION SERVICE      │
│ Port: 8006                 │
│                            │
│ Receives request           │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ VALIDATE REQUEST           │
│ - Check lesson_id          │
│ - Check scenes array       │
│ - Validate scene structure │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ PROCESS EACH SCENE         │
│                            │
│ for scene in scenes:       │
│   process_scene(scene)     │
└────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ SCENE PROCESSING                            │
│                                             │
│ 1. Extract shapes:                          │
│    - type: circle, rect, line, polygon      │
│    - zone: center, left, right, top, bottom │
│    - properties: color, size, position      │
│                                             │
│ 2. Calculate positions:                     │
│    - Canvas: 1920x1080                      │
│    - Zone mapping:                          │
│      center = (960, 540)                    │
│      left = (480, 540)                      │
│      right = (1440, 540)                    │
│      top = (960, 270)                       │
│      bottom = (960, 810)                    │
│                                             │
│ 3. Apply transformations:                   │
│    - Scale shapes                           │
│    - Position elements                      │
│    - Set colors                             │
│                                             │
│ 4. Generate animation keyframes:            │
│    - Start state                            │
│    - End state                              │
│    - Duration                               │
│    - Easing function                        │
│                                             │
│ 5. Add text elements:                       │
│    - Position                               │
│    - Font                                   │
│    - Color                                  │
│                                             │
│ 6. Generate audio:                          │
│    - Text-to-speech for narration           │
│    - Sync with animations                   │
└─────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ CREATE VISUALIZATION DOC   │
│                            │
│ {                          │
│   visualization_id: "...", │
│   lesson_id: lesson_id,    │
│   topic: topic,            │
│   scenes: [                │
│     {                      │
│       scene_id: "...",     │
│       shapes: [...],       │
│       animations: [...],   │
│       text: [...],         │
│       audio: {...},        │
│       canvas: {            │
│         width: 1920,       │
│         height: 1080       │
│       }                    │
│     }                      │
│   ],                       │
│   created_at: UTC now,     │
│   status: "processed"      │
│ }                          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ STORE IN MONGODB           │
│ Collection: visualizations │
│ Database: Gnyansetu_Viz    │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ RETURN RESPONSE            │
│                            │
│ {                          │
│   success: true,           │
│   visualization_id: "...", │
│   scenes_count: 5,         │
│   status: "ready"          │
│ }                          │
└────────────────────────────┘
```

**File**: `microservices/visualization-service/app.py`
- **Endpoint**: `POST /api/visualizations/process`
- **Function**: `process_visualization()` (Line 150)
- **AI Model**: Gemini 2.0 Flash Experimental (for enhancement)
- **Database**: MongoDB `Gnyansetu_Viz.visualizations`

---

## WORKFLOW 5: TEACHING SESSION

### 5.1 TEACHING SESSION FLOW

```
[After Lesson Generated]
         │
         ▼
┌────────────────────────────┐
│ FRONTEND STARTS SESSION    │
│                            │
│ WebSocket Connection to:   │
│ ws://localhost:8004/teach  │
│                            │
│ Params: {                  │
│   lesson_id: "...",        │
│   user_id: "..."           │
│ }                          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ TEACHING SERVICE           │
│ Port: 8004                 │
│                            │
│ WebSocket Handler          │
│ (Django Channels)          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ FETCH LESSON DATA          │
│                            │
│ GET /api/lessons/{id}      │
│ from Lesson Service        │
│                            │
│ Returns: {                 │
│   lesson_content: "...",   │
│   visualization: {...},    │
│   quiz: {...},             │
│   notes: {...}             │
│ }                          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ CREATE SESSION DOCUMENT    │
│                            │
│ sessions.insert({          │
│   session_id: UUID,        │
│   user_id: user_id,        │
│   lesson_id: lesson_id,    │
│   started_at: UTC now,     │
│   status: "active",        │
│   progress: {              │
│     current_section: 0,    │
│     completed: [],         │
│     quiz_score: null       │
│   }                        │
│ })                         │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ SEND LESSON TO FRONTEND    │
│                            │
│ WebSocket Message: {       │
│   type: "lesson_start",    │
│   data: {                  │
│     content: "...",        │
│     sections: [...],       │
│     current: 0             │
│   }                        │
│ }                          │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ DISPLAY INTERACTIVE LESSON │
│ - Render markdown content  │
│ - Show visualizations      │
│ - Enable Konva whiteboard  │
│ - Real-time Q&A            │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ TRACK PROGRESS             │
│                            │
│ Update MongoDB on:         │
│ - Section completed        │
│ - Quiz attempted           │
│ - Notes viewed             │
│ - Time spent               │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ QUIZ SUBMISSION            │
│                            │
│ POST /api/quizzes/submit   │
│ to Quiz Service (8005)     │
│                            │
│ Calculates score           │
│ Returns results            │
└────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ SESSION COMPLETE           │
│                            │
│ Update session:            │
│ - status: "completed"      │
│ - completed_at: UTC now    │
│ - final_score: score       │
│                            │
│ Close WebSocket            │
└────────────────────────────┘
```

**File**: `microservices/teaching-service/teaching/consumers.py`
- **WebSocket Consumer**: `TeachingConsumer`
- **Database**: MongoDB `Gnyansetu_Teaching.sessions`

---

## COMPLETE END-TO-END DATA FLOW

```
USER → FRONTEND → GATEWAY → SERVICES → DATABASE → AI → RESPONSE
 │         │         │          │          │       │       │
 │         │         │          │          │       │       │
 └─────────┴─────────┴──────────┴──────────┴───────┴───────┘
                            │
                            ▼
                    COMPLETE FLOW:

1. USER REGISTRATION (8002)
   Frontend → Gateway → User Service → MongoDB → JWT Token → Frontend

2. PDF UPLOAD (8003)
   Frontend → Gateway → Lesson Service → PDF Processing → MongoDB

3. LESSON GENERATION (8003 + Gemini)
   Lesson Service → Gemini API → Parse Response → MongoDB → Frontend

4. ASYNC QUIZ/NOTES (8003 + Gemini)
   Background Thread → Gemini API → Parse JSON → MongoDB

5. VISUALIZATION (8006 + Gemini)
   Frontend → Viz Service → Process Scenes → MongoDB → Frontend

6. TEACHING SESSION (8004 + WebSocket)
   Frontend WebSocket → Teaching Service → Fetch Lesson → Stream Content

7. QUIZ SUBMISSION (8005)
   Frontend → Quiz Service → Calculate Score → MongoDB → Frontend
```

---

## KEY FILES & FUNCTIONS REFERENCE

### User Service (8002)
- **File**: `microservices/user-service/app.py`
- **Signup**: `signup()` - Line 278
- **Login**: `login()` - Line 378
- **JWT**: `generate_jwt_token()` - Line 106
- **Hash**: `hash_password()` - Line 96

### Lesson Service (8003)
- **Main Endpoint**: `microservices/lesson-service/lessons/views.py`
  - `process_pdf_and_generate_lesson()` - Line 107
- **Lesson Generator**: `microservices/lesson-service/lessons/lesson_generator.py`
  - `generate_lesson()` - Line 100
  - `generate_quiz_data()` - Line 1330
  - `generate_notes_data()` - Line 1517
- **Async**: `views.py` - `generate_quiz_and_notes_async()` - Line 25

### Teaching Service (8004)
- **WebSocket**: `microservices/teaching-service/teaching/consumers.py`
- **Session**: `TeachingConsumer.connect()`

### Quiz Service (8005)
- **Submit**: `microservices/quiz-notes-service/app.py`
- **Calculate Score**: `calculate_quiz_score()`

### Visualization Service (8006)
- **Process**: `microservices/visualization-service/app.py`
- **Endpoint**: `POST /api/visualizations/process`

---

## DATABASE COLLECTIONS

```
MongoDB Databases:
├── Gnyansetu_Users
│   ├── users (user accounts)
│   ├── sessions (login sessions)
│   └── password_resets
│
├── Gnyansetu_Lessons
│   ├── pdf_data (uploaded PDFs)
│   ├── lessons (AI generated lessons)
│   └── user_histories (activity log)
│
├── Gnyansetu_Teaching
│   └── sessions (teaching sessions)
│
├── Gnyansetu_Quiz
│   └── submissions (quiz attempts)
│
└── Gnyansetu_Viz
    └── visualizations (processed viz data)
```

---

## TIMING ANALYSIS

```
Operation                    | Avg Time    | Location
─────────────────────────────┼─────────────┼─────────────────
User Registration            | 50-100ms    | User Service
User Login                   | 50-100ms    | User Service
PDF Upload & Parse           | 500-2000ms  | Lesson Service
AI Lesson Generation         | 3-10s       | Gemini API
Quiz Generation (Async)      | 5-15s       | Gemini API
Notes Generation (Async)     | 5-15s       | Gemini API
Visualization Processing     | 1-5s        | Viz Service
Teaching Session Start       | 100-300ms   | Teaching Service
Quiz Submission              | 50-100ms    | Quiz Service
```

---

This documentation covers the complete workflow from user registration to lesson completion with all technical details, function names, file paths, and data flows.

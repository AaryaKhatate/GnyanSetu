# GnyanSetu_New (gnyansetu_ew)

This is a self-contained, minimal, working copy of the GnyanSetu system created from scratch to provide a reliable baseline you can run locally.

Overview
- Services built with FastAPI (Python) and a small static UI (HTML + JS).
- Ports:
  - API Gateway: http://localhost:8080
  - Lesson Service: http://localhost:8081
  - Visualization Service: http://localhost:8082
  - Quiz/Notes Service: http://localhost:8083
  - UI: open `ui/index.html` in your browser (or run a static server)

Quick start (PowerShell):

```powershell
# Create and activate a venv (if not already)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run all services (opens separate terminals)
.\start_services.bat
```

Notes
- Each service has a `service_doc.md` inside its folder explaining the internals (technical and non-technical), as requested.
- Data is stored in `data/` as JSON files for persistence (no MongoDB required for this baseline).
- The system uses the local Web Speech API for TTS in the UI. If you have a Gemini API key and want server-side generation, the code points are provided to add it.

If anything doesn't work on your machine (ports already used, permission issues), tell me the error logs and I will update the scripts.

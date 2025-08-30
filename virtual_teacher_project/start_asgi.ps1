# PowerShell script to start ASGI server with proper environment
$env:DJANGO_SETTINGS_MODULE = "virtual_teacher_project.settings"
cd "d:\GnyanSetu\virtual_teacher_project"
python -m daphne -b localhost -p 8001 virtual_teacher_project.asgi:application

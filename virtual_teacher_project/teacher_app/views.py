from django.shortcuts import render

def teacher_view(request):
    return render(request, "teacher_app/teacher.html")
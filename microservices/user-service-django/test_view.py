from django.http import JsonResponse

def simple_test(request):
    return JsonResponse({'message': 'Django is working!', 'status': 'ok'})
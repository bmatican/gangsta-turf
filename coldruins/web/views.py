from django.http import HttpResponse

def home(request):
    return HttpResponse(
        open('coldruins/web/index.html', 'rt').read())

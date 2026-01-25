from django.shortcuts import render

def content_index(request):
    return render(request, "content/main/index.html")
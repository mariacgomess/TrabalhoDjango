from django.shortcuts import render, HttpResponse
from .models import TodoItem
# Create your views here.
def home(request):
    #return HttpResponse("hello world!")
    return render(request, "base.html") 
def todos(request):
    items= TodoItem.objects.all()
    return render (request, "todos.html", {"todos":items})
def login(request):
    return render (request,"login.html")
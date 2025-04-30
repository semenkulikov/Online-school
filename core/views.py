from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return HttpResponse('<h1>Service started successfully!</h1><h2>Сервис запущен успешно!</h2>')

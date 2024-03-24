from django.shortcuts import render
from .models import Record, Author


def home(request):
    return render(request, 'home.html', {})


def search(request):
    records = Record.objects.all()
    return render(request, 'search.html', {'records': records})

from django.contrib import admin

# Register your models here.
from .models import Author, Record

admin.site.register(Author)
admin.site.register(Record)

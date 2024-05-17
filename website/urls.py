from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search_results/', views.search, name='search_results'),
    path('search_results/', views.search_results, name='search_results'),
    path('upload_pdf/', views.upload_pdf, name='upload_pdf'),
    path('download_csv/', views.download_csv, name='download_csv'),
]


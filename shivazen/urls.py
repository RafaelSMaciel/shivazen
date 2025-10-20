# shivazen/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Rota para a interface de admin
    path('', include('app_shivazen.urls')),
]
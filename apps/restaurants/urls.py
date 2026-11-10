from django.urls import path
from . import views

app_name = 'restaurants'

urlpatterns = [
    path('settings/', views.restaurant_settings, name='settings'),
]

from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.meal_list, name='meal_list'),
    path('categories/', views.category_list, name='category_list'),
    path('create/', views.meal_create, name='meal_create'),
    path('<int:meal_id>/edit/', views.meal_edit, name='meal_edit'),
    path('<int:meal_id>/toggle/', views.meal_toggle_availability, name='meal_toggle'),
    path('api/meals/', views.api_meals, name='api_meals'),
]

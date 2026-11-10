from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard_redirect'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]

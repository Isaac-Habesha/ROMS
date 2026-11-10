from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('orders/', views.all_orders, name='all_orders'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/export/csv/', views.export_report_csv, name='export_report_csv'),
    path('reports/export/pdf/', views.export_report_pdf, name='export_report_pdf'),
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/toggle/', views.user_toggle_status, name='user_toggle_status'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
]


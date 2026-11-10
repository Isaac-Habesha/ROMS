from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    path('', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('update-status/<int:order_id>/', views.update_status, name='update_status'),
    path('ticket/<int:order_id>/', views.print_ticket, name='print_ticket'),
    path('ticket/<int:order_id>/record-print/', views.record_print, name='record_print'),
    path('api/orders/', views.active_orders_api, name='active_orders_api'),
]


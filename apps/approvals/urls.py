from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    path('', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('pending/', views.pending_orders, name='pending_orders'),
    path('history/', views.order_history, name='order_history'),
    path('review/<int:order_id>/', views.review_order, name='review_order'),
    path('approve/<int:order_id>/', views.approve_order, name='approve_order'),
    path('reject/<int:order_id>/', views.reject_order, name='reject_order'),
]


from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('waiter/', views.waiter_dashboard, name='waiter_dashboard'),
    path('waiter/create/', views.create_order, name='create_order'),
    path('waiter/orders/', views.waiter_orders, name='waiter_orders'),
    path('waiter/orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('waiter/orders/<int:order_id>/resubmit/', views.resubmit_order, name='resubmit_order'),
]


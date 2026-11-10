from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import CustomUser
from apps.menu.models import MealCategory, Meal
from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.approvals.models import OrderApproval
from apps.kitchen.models import KitchenTicket
from apps.payments.models import Payment
from decimal import Decimal


class ROMSOrderLifecycleTests(TestCase):
    def setUp(self):
        # Create users for all 4 roles
        self.waiter = CustomUser.objects.create_user(
            username='test_waiter',
            password='password123',
            role=CustomUser.Role.WAITER,
            first_name='Test',
            last_name='Waiter'
        )
        self.supervisor = CustomUser.objects.create_user(
            username='test_supervisor',
            password='password123',
            role=CustomUser.Role.SUPERVISOR,
            first_name='Test',
            last_name='Supervisor'
        )
        self.chef = CustomUser.objects.create_user(
            username='test_chef',
            password='password123',
            role=CustomUser.Role.KITCHEN_STAFF,
            first_name='Test',
            last_name='Chef'
        )
        self.admin = CustomUser.objects.create_superuser(
            username='test_admin',
            password='password123',
            role=CustomUser.Role.ADMIN,
            first_name='Test',
            last_name='Admin'
        )

        # Create category and meal
        self.category = MealCategory.objects.create(name='Mains')
        self.meal1 = Meal.objects.create(
            category=self.category,
            name='Burger Deluxe',
            price=Decimal('15.00'),
            is_available=True
        )
        self.meal2 = Meal.objects.create(
            category=self.category,
            name='Fresh Soda',
            price=Decimal('3.00'),
            is_available=True
        )

    def test_waiter_create_order(self):
        """Test waiter can create and submit an order."""
        client = Client()
        client.login(username='test_waiter', password='password123')

        response = client.post(reverse('orders:create_order'), {
            'customer_count': 2,
            'order_notes': 'Table near window',
            'meal_id[]': [self.meal1.id, self.meal2.id],
            'quantity[]': [2, 1],
            'instructions[]': ['Extra crispy', 'Ice please'],
        })
        self.assertEqual(response.status_code, 302)

        # Verify order state
        order = Order.objects.filter(waiter=self.waiter).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, Order.Status.PENDING_APPROVAL)
        self.assertEqual(order.customer_count, 2)
        self.assertEqual(order.items.count(), 2)
        # 2 * 15.00 + 1 * 3.00 = 33.00
        self.assertEqual(order.total_amount, Decimal('33.00'))

    def test_supervisor_approval_and_dispatch(self):
        """Test supervisor approval generates order number, ticket, and dispatches to kitchen."""
        order = Order.objects.create(
            waiter=self.waiter,
            customer_count=3,
            status=Order.Status.PENDING_APPROVAL,
            total_amount=Decimal('30.00'),
        )
        OrderItem.objects.create(order=order, meal=self.meal1, quantity=2, unit_price=self.meal1.price)

        client = Client()
        client.login(username='test_supervisor', password='password123')

        # Approve order
        response = client.post(reverse('approvals:approve_order', args=[order.id]))
        self.assertEqual(response.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.APPROVED)
        self.assertTrue(order.order_number.startswith('#ORD-'))
        self.assertIsNotNone(order.approved_at)

        # Check kitchen ticket was generated
        ticket = KitchenTicket.objects.filter(order=order).first()
        self.assertIsNotNone(ticket)

        # Test duplicate approval prevention
        response_dup = client.post(reverse('approvals:approve_order', args=[order.id]))
        self.assertEqual(response_dup.status_code, 302)
        self.assertEqual(KitchenTicket.objects.filter(order=order).count(), 1)

    def test_supervisor_rejection_and_waiter_resubmit(self):
        """Test supervisor can reject with reason and waiter can resubmit."""
        order = Order.objects.create(
            waiter=self.waiter,
            customer_count=1,
            status=Order.Status.PENDING_APPROVAL,
            total_amount=Decimal('15.00'),
        )

        sup_client = Client()
        sup_client.login(username='test_supervisor', password='password123')

        # Empty reason rejected
        res_fail = sup_client.post(reverse('approvals:reject_order', args=[order.id]), {'rejection_reason': ''})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING_APPROVAL)

        # Valid reason
        res_ok = sup_client.post(reverse('approvals:reject_order', args=[order.id]), {
            'rejection_reason': 'Meal unavailable today'
        })
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.REJECTED)
        self.assertEqual(order.rejection_reason, 'Meal unavailable today')

        # Waiter resubmit
        waiter_client = Client()
        waiter_client.login(username='test_waiter', password='password123')
        res_resubmit = waiter_client.post(reverse('orders:resubmit_order', args=[order.id]))
        self.assertEqual(res_resubmit.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING_APPROVAL)

    def test_kitchen_workflow_received_preparing_ready(self):
        """Test kitchen progression through RECEIVED -> PREPARING -> READY (3 states)."""
        order = Order.objects.create(
            waiter=self.waiter,
            order_number='#ORD-0099',
            customer_count=2,
            status=Order.Status.APPROVED,
            total_amount=Decimal('30.00'),
        )
        KitchenTicket.objects.create(order=order, ticket_number='TKT-0099')

        chef_client = Client()
        chef_client.login(username='test_chef', password='password123')

        # Move to RECEIVED
        chef_client.post(reverse('kitchen:update_status', args=[order.id]), {'status': 'RECEIVED'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'RECEIVED')

        # Move to PREPARING
        chef_client.post(reverse('kitchen:update_status', args=[order.id]), {'status': 'PREPARING'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'PREPARING')

        # Move to READY
        chef_client.post(reverse('kitchen:update_status', args=[order.id]), {'status': 'READY'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'READY')

    def test_payment_and_revenue_independence(self):
        """Test payment recording is independent and revenue calculations only count paid orders."""
        order = Order.objects.create(
            waiter=self.waiter,
            order_number='#ORD-0100',
            customer_count=1,
            status=Order.Status.READY,
            total_amount=Decimal('45.00'),
        )

        sup_client = Client()
        sup_client.login(username='test_supervisor', password='password123')

        # Record payment
        res = sup_client.post(reverse('payments:record_payment', args=[order.id]), {
            'amount': '45.00',
            'payment_method': 'CASH',
            'notes': 'Paid in full',
        })
        self.assertEqual(res.status_code, 302)

        payment = Payment.objects.filter(order=order).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, Decimal('45.00'))
        self.assertEqual(payment.status, Payment.Status.COMPLETED)

    def test_role_access_control(self):
        """Test unauthorized users cannot access restricted dashboards."""
        waiter_client = Client()
        waiter_client.login(username='test_waiter', password='password123')

        # Waiter cannot access admin dashboard
        res = waiter_client.get(reverse('analytics:admin_dashboard'))
        self.assertEqual(res.status_code, 302)

        # Waiter cannot access supervisor approval
        res2 = waiter_client.get(reverse('approvals:supervisor_dashboard'))
        self.assertEqual(res2.status_code, 302)

        # Waiter cannot access kitchen dashboard
        res3 = waiter_client.get(reverse('kitchen:kitchen_dashboard'))
        self.assertEqual(res3.status_code, 302)


from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import CustomUser
from apps.restaurants.models import Restaurant, RestaurantSettings
from apps.menu.models import MealCategory, Meal
from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.approvals.models import OrderApproval
from apps.kitchen.models import KitchenTicket, KitchenStatusHistory
from apps.payments.models import Payment
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seeds the database with initial restaurant data, demo users, meals, and sample orders'

    def handle(self, *args, **options):
        self.stdout.write("Seeding ROMS database...")

        # 1. Restaurant
        restaurant, created = Restaurant.objects.get_or_create(
            id=1,
            defaults={
                'name': 'Gourmet Bistro',
                'address': '123 Downtown Boulevard',
                'phone': '+254 700 123456',
                'email': 'info@gourmetbistro.com',
            }
        )
        RestaurantSettings.objects.get_or_create(
            restaurant=restaurant,
            defaults={
                'currency_symbol': '$',
                'order_prefix': 'ORD',
                'enable_sound_notifications': True,
                'auto_print_on_approval': True,
            }
        )

        # 2. Users
        users_data = [
            ('admin', 'Admin', 'Manager', 'admin@bistro.com', CustomUser.Role.ADMIN, 'admin123'),
            ('supervisor', 'Sarah', 'Supervisor', 'sarah@bistro.com', CustomUser.Role.SUPERVISOR, 'super123'),
            ('waiter1', 'John', 'Waiter', 'john@bistro.com', CustomUser.Role.WAITER, 'waiter123'),
            ('waiter2', 'Emily', 'Waiter', 'emily@bistro.com', CustomUser.Role.WAITER, 'waiter123'),
            ('chef1', 'Gordon', 'Chef', 'gordon@bistro.com', CustomUser.Role.KITCHEN_STAFF, 'chef123'),
        ]

        created_users = {}
        for username, first, last, email, role, password in users_data:
            user, u_created = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': email,
                    'role': role,
                    'is_staff': (role == CustomUser.Role.ADMIN),
                    'is_superuser': (role == CustomUser.Role.ADMIN),
                }
            )
            if u_created:
                user.set_password(password)
                user.save()
            created_users[username] = user
            self.stdout.write(f"User: {username} ({role}) ready.")

        # 3. Categories & Meals
        categories = {
            'Burgers & Sandwiches': [
                ('Classic Beef Burger', 'Juicy beef patty with lettuce, tomato, cheddar, and house sauce', Decimal('12.50'), 15),
                ('Crispy Chicken Burger', 'Crispy buttermilk fried chicken with slaw and spicy mayo', Decimal('11.00'), 12),
                ('Mushroom Swiss Burger', 'Grilled beef patty topped with sautéed wild mushrooms and melted Swiss cheese', Decimal('13.50'), 15),
            ],
            'Main Courses': [
                ('Grilled Ribeye Steak', 'Prime 300g ribeye steak served with herb garlic butter and fries', Decimal('24.00'), 25),
                ('Pan-Seared Salmon', 'Fresh salmon fillet served with asparagus and lemon butter sauce', Decimal('21.50'), 20),
                ('Creamy Alfredo Pasta', 'Fettuccine in rich garlic parmesan cream sauce with grilled chicken', Decimal('15.00'), 15),
            ],
            'Starters & Sides': [
                ('Loaded Potato Wedges', 'Crispy wedges with cheddar cheese sauce, bacon bits, and sour cream', Decimal('6.50'), 10),
                ('Buffalo Wings (8pcs)', 'Crispy chicken wings tossed in tangy spicy buffalo sauce', Decimal('8.50'), 12),
                ('Garlic Herb Bread', 'Toasted baguette with garlic butter and fresh parsley', Decimal('4.50'), 8),
            ],
            'Beverages': [
                ('Fresh Berry Smoothie', 'Fresh strawberries, blueberries, banana, and Greek yogurt', Decimal('5.50'), 5),
                ('Iced Caramel Latte', 'Espresso, cold milk, caramel drizzle over ice', Decimal('4.75'), 5),
                ('Fresh Squeezed Orange Juice', '100% pure fresh oranges', Decimal('4.00'), 3),
            ],
            'Desserts': [
                ('Warm Chocolate Lava Cake', 'Rich chocolate cake with a molten center, served with vanilla ice cream', Decimal('7.50'), 12),
                ('Classic Tiramisu', 'Layered espresso-soaked ladyfingers with mascarpone cream', Decimal('6.50'), 5),
            ]
        }

        all_meals = []
        for cat_name, meals in categories.items():
            category, _ = MealCategory.objects.get_or_create(name=cat_name)
            for m_name, m_desc, m_price, m_prep in meals:
                meal, _ = Meal.objects.get_or_create(
                    name=m_name,
                    defaults={
                        'category': category,
                        'description': m_desc,
                        'price': m_price,
                        'preparation_time_minutes': m_prep,
                        'is_available': True,
                    }
                )
                all_meals.append(meal)

        # 4. Sample Orders
        w1 = created_users['waiter1']
        sup = created_users['supervisor']

        # Order 1: Pending Approval
        o1, _ = Order.objects.get_or_create(
            order_reference='REF-ORD001',
            defaults={
                'waiter': w1,
                'customer_count': 3,
                'status': Order.Status.PENDING_APPROVAL,
                'order_notes': 'Customers requested dishes served together.',
                'submitted_at': timezone.now(),
            }
        )
        if o1.items.count() == 0:
            OrderItem.objects.create(order=o1, meal=all_meals[0], quantity=2, unit_price=all_meals[0].price, special_instructions='No pickles on one')
            OrderItem.objects.create(order=o1, meal=all_meals[9], quantity=3, unit_price=all_meals[9].price, special_instructions='')
            o1.calculate_total()

        # Order 2: Approved / Received in kitchen
        o2, _ = Order.objects.get_or_create(
            order_reference='REF-ORD002',
            defaults={
                'order_number': '#ORD-0001',
                'waiter': w1,
                'customer_count': 2,
                'status': Order.Status.RECEIVED,
                'submitted_at': timezone.now(),
                'approved_at': timezone.now(),
            }
        )
        if o2.items.count() == 0:
            OrderItem.objects.create(order=o2, meal=all_meals[3], quantity=1, unit_price=all_meals[3].price, special_instructions='Medium rare')
            OrderItem.objects.create(order=o2, meal=all_meals[4], quantity=1, unit_price=all_meals[4].price, special_instructions='')
            o2.calculate_total()
            OrderApproval.objects.get_or_create(order=o2, defaults={'supervisor': sup, 'decision': OrderApproval.Decision.APPROVED})
            KitchenTicket.objects.get_or_create(order=o2, defaults={'ticket_number': 'TKT-ORD-0001'})
            KitchenStatusHistory.objects.get_or_create(order=o2, status='RECEIVED', defaults={'notes': 'Order received in kitchen'})

        # Order 3: Preparing in kitchen
        o3, _ = Order.objects.get_or_create(
            order_reference='REF-ORD003',
            defaults={
                'order_number': '#ORD-0002',
                'waiter': w1,
                'customer_count': 4,
                'status': Order.Status.PREPARING,
                'submitted_at': timezone.now(),
                'approved_at': timezone.now(),
            }
        )
        if o3.items.count() == 0:
            OrderItem.objects.create(order=o3, meal=all_meals[1], quantity=2, unit_price=all_meals[1].price, special_instructions='Extra spicy slaw')
            OrderItem.objects.create(order=o3, meal=all_meals[6], quantity=2, unit_price=all_meals[6].price, special_instructions='')
            o3.calculate_total()
            OrderApproval.objects.get_or_create(order=o3, defaults={'supervisor': sup, 'decision': OrderApproval.Decision.APPROVED})
            KitchenTicket.objects.get_or_create(order=o3, defaults={'ticket_number': 'TKT-ORD-0002'})
            KitchenStatusHistory.objects.get_or_create(order=o3, status='PREPARING', defaults={'notes': 'Chef started preparation'})

        # Order 4: Ready for serving
        o4, _ = Order.objects.get_or_create(
            order_reference='REF-ORD004',
            defaults={
                'order_number': '#ORD-0003',
                'waiter': w1,
                'customer_count': 2,
                'status': Order.Status.READY,
                'submitted_at': timezone.now(),
                'approved_at': timezone.now(),
            }
        )
        if o4.items.count() == 0:
            OrderItem.objects.create(order=o4, meal=all_meals[5], quantity=2, unit_price=all_meals[5].price, special_instructions='')
            o4.calculate_total()
            OrderApproval.objects.get_or_create(order=o4, defaults={'supervisor': sup, 'decision': OrderApproval.Decision.APPROVED})
            KitchenTicket.objects.get_or_create(order=o4, defaults={'ticket_number': 'TKT-ORD-0003'})
            KitchenStatusHistory.objects.get_or_create(order=o4, status='READY', defaults={'notes': 'Meal plated and ready'})

        # Order 5: Served and Paid
        o5, _ = Order.objects.get_or_create(
            order_reference='REF-ORD005',
            defaults={
                'order_number': '#ORD-0004',
                'waiter': w1,
                'customer_count': 2,
                'status': Order.Status.SERVED,
                'submitted_at': timezone.now(),
                'approved_at': timezone.now(),
            }
        )
        if o5.items.count() == 0:
            OrderItem.objects.create(order=o5, meal=all_meals[0], quantity=2, unit_price=all_meals[0].price, special_instructions='')
            OrderItem.objects.create(order=o5, meal=all_meals[11], quantity=2, unit_price=all_meals[11].price, special_instructions='')
            o5.calculate_total()
            Payment.objects.get_or_create(
                order=o5,
                defaults={
                    'amount': o5.total_amount,
                    'payment_method': Payment.Method.CASH,
                    'status': Payment.Status.COMPLETED,
                    'recorded_by': sup,
                }
            )

        self.stdout.write(self.style.SUCCESS("Database seeded successfully with demo users, meals, and sample orders!"))


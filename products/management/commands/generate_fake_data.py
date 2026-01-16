"""
Management command to generate fake data for testing.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
import random

from products.models import Category, Product
from orders.models import Order, OrderItem


class Command(BaseCommand):
    help = 'Generate fake data for testing purposes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Number of fake users to create'
        )
        parser.add_argument(
            '--categories',
            type=int,
            default=3,
            help='Number of fake categories to create'
        )
        parser.add_argument(
            '--products',
            type=int,
            default=20,
            help='Number of fake products to create'
        )
        parser.add_argument(
            '--orders',
            type=int,
            default=10,
            help='Number of fake orders to create'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating'
        )
    
    def handle(self, *args, **options):
        fake = Faker()
        User = get_user_model()
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
        
        # Create users
        self.stdout.write(f'Creating {options["users"]} users...')
        users = []
        for i in range(options['users']):
            user = User.objects.create_user(
                email=fake.email(),
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone=fake.phone_number()[:20],
                department=fake.job(),
                position=fake.job(),
            )
            if i == 0:
                user.is_staff = True
                user.save()
            users.append(user)
        
        # Create categories
        self.stdout.write(f'Creating {options["categories"]} categories...')
        categories = []
        for i in range(options['categories']):
            category = Category.objects.create(
                name=fake.word().title(),
                description=fake.paragraph()
            )
            categories.append(category)
        
        # Create products
        self.stdout.write(f'Creating {options["products"]} products...')
        products = []
        statuses = ['active', 'active', 'active', 'inactive', 'out_of_stock']
        
        for i in range(options['products']):
            product = Product.objects.create(
                sku=f'FAKE-{fake.random_number(digits=6)}',
                name=fake.catch_phrase(),
                description=fake.paragraph(),
                category=random.choice(categories),
                price=random.uniform(10, 1000),
                cost=random.uniform(5, 500),
                quantity=random.randint(0, 500),
                min_quantity=random.randint(5, 20),
                max_quantity=random.randint(100, 1000),
                status=random.choice(statuses),
                created_by=random.choice(users),
                updated_by=random.choice(users),
            )
            products.append(product)
        
        # Create orders
        self.stdout.write(f'Creating {options["orders"]} orders...')
        order_statuses = ['draft', 'pending', 'processing', 'shipped', 'delivered', 'cancelled']
        
        for i in range(options['orders']):
            order = Order.objects.create(
                customer_name=fake.name(),
                customer_email=fake.email(),
                customer_phone=fake.phone_number()[:20],
                customer_address=fake.address(),
                status=random.choice(order_statuses),
                notes=fake.paragraph() if random.choice([True, False]) else '',
                created_by=random.choice(users),
                assigned_to=random.choice(users) if random.choice([True, False]) else None,
                total_amount=0,
                final_amount=0,
            )
            
            # Add items to order - ensure unique products per order
            num_items = random.randint(1, min(5, len(products)))
            selected_products = random.sample(products, num_items)
            
            for product in selected_products:
                quantity = random.randint(1, min(10, product.quantity if product.quantity > 0 else 1))
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price
                )
            
            order.update_totals()
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created: {len(users)} users, '
            f'{len(categories)} categories, '
            f'{len(products)} products, '
            f'{options["orders"]} orders'
        ))

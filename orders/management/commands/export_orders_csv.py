"""
Management command to export orders to CSV.
"""

import csv
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Count

from orders.models import Order
from products.models import Product


class Command(BaseCommand):
    help = 'Export orders to CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--filename',
            type=str,
            default=f'orders_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv',
            help='Output filename'
        )
        parser.add_argument(
            '--status',
            type=str,
            help='Filter by order status'
        )
        parser.add_argument(
            '--date-from',
            type=str,
            help='Filter by start date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--date-to',
            type=str,
            help='Filter by end date (YYYY-MM-DD)'
        )
    
    def handle(self, *args, **options):
        # Build query
        queryset = Order.objects.all().select_related('created_by', 'assigned_to')
        
        if options['status']:
            queryset = queryset.filter(status=options['status'])
        
        if options['date_from']:
            queryset = queryset.filter(created_at__date__gte=options['date_from'])
        
        if options['date_to']:
            queryset = queryset.filter(created_at__date__lte=options['date_to'])
        
        # Create CSV file
        filename = options['filename']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'Order Number',
                'Customer Name',
                'Customer Email',
                'Customer Phone',
                'Status',
                'Total Amount',
                'Tax Amount',
                'Discount Amount',
                'Final Amount',
                'Created At',
                'Created By',
                'Assigned To',
                'Completed At',
                'Items Count',
                'Notes',
            ])
            
            # Write data
            for order in queryset:
                items_count = order.items.count()
                
                writer.writerow([
                    order.order_number,
                    order.customer_name,
                    order.customer_email,
                    order.customer_phone or '',
                    order.status,
                    str(order.total_amount),
                    str(order.tax_amount),
                    str(order.discount_amount),
                    str(order.final_amount),
                    order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    order.created_by.email,
                    order.assigned_to.email if order.assigned_to else '',
                    order.completed_at.strftime('%Y-%m-%d %H:%M:%S') if order.completed_at else '',
                    items_count,
                    order.notes.replace('\n', ' ') if order.notes else '',
                ])
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully exported {queryset.count()} orders to {filename}'
        ))
        
        # Display statistics
        self.stdout.write('\nExport Statistics:')
        self.stdout.write(f'Total Orders: {queryset.count()}')
        
        if queryset.exists():
            total_revenue = queryset.aggregate(Sum('final_amount'))['final_amount__sum'] or 0
            avg_order_value = total_revenue / queryset.count()
            
            self.stdout.write(f'Total Revenue: ${total_revenue:.2f}')
            self.stdout.write(f'Average Order Value: ${avg_order_value:.2f}')
            
            # Status breakdown
            self.stdout.write('\nStatus Breakdown:')
            status_counts = queryset.values('status').annotate(count=Count('id'))
            for stat in status_counts:
                self.stdout.write(f'  {stat["status"]}: {stat["count"]}')

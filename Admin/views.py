from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import AdminLoginForm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io 
import base64
from django.conf import settings
from django.urls import reverse
from functools import wraps
from Products.models import ProductVariant
from Orders.models import Order, OrderItem
from Coupons.models import Coupon
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json
import csv
from django.http import HttpResponse
from django.template.loader import render_to_string,get_template # type: ignore
from xhtml2pdf import pisa # type: ignore
from io import BytesIO
from Category.models import Category



# Create your views here.

def admin_login(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            if email == settings.ADMIN_EMAIL and password == settings.ADMIN_PASSWORD:
                request.session['is_admin'] = True
                return redirect(reverse('dashboard'))
            else:
                messages.error(request, 'Invalid Email and Password')
        else:
            messages.error(request, 'Invalid Form')
    else:
        form = AdminLoginForm()
    return render(request,'Admin/admin_login.html', {'form' : form})


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view_func(request, *args, **kwargs):
        if request.session.get('is_admin'):
            return view_func(request, *args, **kwargs)
        return redirect('admin_login')
    return _wrapped_view_func

@admin_required
def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@admin_required
def admin_dashboard(request):
    #Get the date range from request parameters or use default (last 30 days)
    date_range = request.GET.get('date_range', '30')
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(date_range))

    # Fetch orders within the date range 
    orders = Order.objects.filter(created_at__range = (start_date, end_date))

    # Calculate total sales and count
    total_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    order_count = orders.count()

    #Get daily sales data 
    daily_sales = orders.values('created_at__date').annotate(
        total = Sum('total_amount'),
        count = Count('id')
    ).order_by('created_at__date')

    #Generate sales graph
    sales_graph = generate_sales_graph(daily_sales)

    # Prepare data for the sales graph
    sales_dates = [item['created_at__date'].strftime('%Y-%m-%d') for item in daily_sales ]
    sales_amounts = [float(item['total']) for item in daily_sales]

    # Get best selling products
    best_selling_products = get_best_selling_products(start_date, end_date)


    # Get best selling categories
    best_selling_categories = get_best_selling_categories(start_date, end_date)
    context = {
        'total_sales': total_sales,
        'order_count': order_count,
        'sales_dates': json.dumps(sales_dates),
        'sales_amounts': json.dumps(sales_amounts),
        'best_selling_products': best_selling_products,
        'date_range': date_range,
        'best_selling_categories' : best_selling_categories,
    }
    return render(request, 'Admin/admin_dashboard.html', context)

def generate_sales_graph(daily_sales):
    dates = [item['created_at__date'] for item in daily_sales]
    amounts = [item['total'] for item in daily_sales]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, amounts)
    plt.title('Daily Sales')
    plt.xlabel('Date')
    plt.ylabel('Total Sales')
    plt.xticks(rotation = 45)
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format = 'png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    plt.close()  # This closes the plot and clears the memory

    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic

def get_best_selling_products(start_date, end_date):
    return ProductVariant.objects.filter(
        orderitem__order__created_at__range = (start_date, end_date)
    ).annotate(
        sold = Sum('orderitem__quantity')
    ).order_by('-sold')[:5]

# Add this new function in the same views.py file
def get_best_selling_categories(start_date, end_date):
    return Category.objects.filter(
        # Filter for orders in date range
        product__variants__orderitem__order__created_at__range=(start_date, end_date),
        # Only active categories
        status='active',
        is_delete=False,
        # Only active products
        product__status='Active',
        product__is_delete=False,
        # Only active variants
        product__variants__status='Active'
    ).annotate(
        sold=Sum('product__variants__orderitem__quantity'),
        total_products=Count('product', filter=Q(
            product__status='Active',
            product__is_delete=False
        ), distinct=True),
        active_variants=Count('product__variants', filter=Q(
            product__variants__status='Active'
        ), distinct=True)
    ).filter(
        sold__isnull=False
    ).order_by('-sold')[:5]


def sales_report(request):
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    filter_type = request.GET.get('filter_type', 'custom')

    # Set date range based on filter type
    if filter_type == 'day':
        start_date = end_date = datetime.now().date()
    elif filter_type == 'week':
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
    elif filter_type == 'month':
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    else:  # custom date range
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None

    # Fetch orders within the date range
    orders = Order.objects.filter(created_at__date__range=[start_date, end_date])

    # Calculate report data
    total_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    order_count = orders.count()
    total_discount = orders.aggregate(Sum('discount'))['discount__sum'] or 0

    # Count orders with coupons
    orders_with_coupons = orders.exclude(coupon__isnull=True).count()

    # Prepare data for the report
    report_data = {
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'order_count': order_count,
        'total_discount': total_discount,
        'orders_with_coupons': orders_with_coupons,
        'orders': orders,
    }

    # Generate report based on format
    report_format = request.GET.get('format', 'html')
    if report_format == 'pdf':
        return generate_pdf_report(report_data)
    elif report_format == 'excel':
        return generate_excel_report(report_data)
    else:
        return render(request, 'Admin/sales_report.html', report_data)



def generate_pdf_report(data):
    template = get_template('Admin/sales_report_pdf.html')
    html_string = template.render(data)
    
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result, encoding='UTF-8')
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
        return response
    return HttpResponse('Error generating PDF', status=400)

def generate_excel_report(data):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Start Date', 'End Date', 'Total Sales', 'Order Count', 'Total Discount', 'Orders with Coupons'])
    writer.writerow([
        data['start_date'],
        data['end_date'],
        data['total_sales'],
        data['order_count'],
        data['total_discount'],
        data['orders_with_coupons']
    ])
    
    writer.writerow([])
    writer.writerow(['Order ID', 'Date', 'Total Amount', 'Discount', 'Coupon Used'])
    for order in data['orders']:
        writer.writerow([
            order.id,
            order.created_at.date(),
            order.total_amount,
            order.discount,
            'Yes' if order.coupon else 'No'
        ])
    
    return response


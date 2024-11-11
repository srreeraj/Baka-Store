from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Coupon
from .forms import CouponForm
from django.urls import reverse


# Create your views here.

def coupon_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        coupon_list = Coupon.objects.filter(Q(code_icontains = search_query))
    else:
        coupon_list = Coupon.objects.all()
    
    paginator = Paginator(coupon_list, 10)
    page_number = request.GET.get('page')

    try:
        coupons = paginator.page(page_number)
    except PageNotAnInteger:
        coupons = paginator.page(1)
    except EmptyPage:
        coupons = paginator.page(paginator.num_pages)

    context = {
        'coupons' : coupons
    }

    return render(request, 'Admin/coupon_list.html', context)

def add_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('coupons')
    else:
        form = CouponForm
    return render(request, 'Admin/add_edit_coupon.html', {'form' : form})

def edit_coupon(request, pk):
    coupon = get_object_or_404(Coupon, pk = pk)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            return redirect('coupons')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'Admin/add_edit_coupon.html', {'form' : form})

# def delete_coupon(request, pk):
#     coupon = get_object_or_404(Coupon, pk = pk)
#     current_page = request.GET.get('page', 1)
#     if request.method == 'POST':
#         coupon.delete()
#         return redirect(f'{reverse("coupon-list")}?page={current_page}')
#     context = {
#         'coupon' : coupon,
#         'current_page' : current_page
#     }
#     return render(request, 'Admin/delete_coupon.html', context)




from django.urls import path
from . import views


urlpatterns = [
    path('',views.admin_login,name= 'admin_login'),
    path('admin-logout/',views.admin_logout,name='admin_logout'),
    path('admin-dashboard/',views.admin_dashboard,name = 'dashboard'),
    path('admin-generate-sales-graph/', views.generate_sales_graph, name = 'generate_sales_graph'),
    path('admin-best-selling-products/', views.get_best_selling_products, name='get_best_selling_products'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('generate_pdf_report/', views.generate_pdf_report, name='generate_pdf_report'),
    path('generate-excel-report/', views.generate_excel_report, name='generate_excel_report'),
]
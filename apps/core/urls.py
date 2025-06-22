from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Vendedores
    path('salespersons/', views.SalesPersonListView.as_view(), name='salesperson_list'),
    path('salespersons/create/', views.SalesPersonCreateView.as_view(), name='salesperson_create'),
    path('salespersons/<int:pk>/', views.SalesPersonDetailView.as_view(), name='salesperson_detail'),
    path('salespersons/<int:pk>/edit/', views.SalesPersonUpdateView.as_view(), name='salesperson_update'),
    path('salespersons/<int:pk>/delete/', views.SalesPersonDeleteView.as_view(), name='salesperson_delete'),
    
    # Perfiles de Empresa
    path('company/', views.CompanyProfileListView.as_view(), name='company_list'),
    path('company/create/', views.CompanyProfileCreateView.as_view(), name='company_create'),
    path('company/<int:pk>/', views.CompanyProfileDetailView.as_view(), name='company_detail'),
    path('company/<int:pk>/edit/', views.CompanyProfileUpdateView.as_view(), name='company_update'),
    path('company/<int:pk>/delete/', views.CompanyProfileDeleteView.as_view(), name='company_delete'),
    
    # Configuración del Sistema
    path('settings/', views.SystemSettingsUpdateView.as_view(), name='system_settings'),
] 
from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View
from django.db.models import Count, Sum, Q
from django.urls import reverse_lazy
from django.contrib import messages
from apps.quotations.models import Quotation
from apps.clients.models import Client
from apps.services.models import Service
from .models import SalesPerson, CompanyProfile
from decimal import Decimal

# Create your views here.

class CustomLogoutView(View):
    """Custom logout view that handles both GET and POST requests"""
    
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('login')
    
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('login')

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        context['total_quotations'] = Quotation.objects.count()
        context['total_clients'] = Client.objects.count()
        context['total_services'] = Service.objects.count()
        
        # Estadísticas de cotizaciones por estado
        quotation_stats = Quotation.objects.aggregate(
            draft=Count('id', filter=Q(status='draft')),
            sent=Count('id', filter=Q(status='sent')),
            accepted=Count('id', filter=Q(status='accepted')),
            rejected=Count('id', filter=Q(status='rejected')),
            expired=Count('id', filter=Q(status='expired'))
        )
        context['quotation_stats'] = quotation_stats
        
        # Valor total de cotizaciones (calculado manualmente ya que total_amount es una propiedad)
        total_value = Decimal('0.00')
        for quotation in Quotation.objects.all():
            total_value += quotation.total_amount
        context['total_value'] = total_value
        
        # Cotizaciones recientes
        context['recent_quotations'] = Quotation.objects.select_related('client').order_by('-created_at')[:5]
        
        # Clientes recientes
        context['recent_clients'] = Client.objects.order_by('-created_at')[:5]
        
        return context

# Vistas para Vendedores
class SalesPersonListView(LoginRequiredMixin, ListView):
    model = SalesPerson
    template_name = 'core/salesperson/list.html'
    context_object_name = 'salespersons'
    paginate_by = 20
    ordering = ['first_name', 'last_name']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por estado activo/inactivo
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Búsqueda por nombre o email
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status')
        context['current_search'] = self.request.GET.get('search', '')
        return context

class SalesPersonDetailView(LoginRequiredMixin, DetailView):
    model = SalesPerson
    template_name = 'core/salesperson/detail.html'
    context_object_name = 'salesperson'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        salesperson = self.get_object()
        
        # Estadísticas del vendedor
        context['quotations_count'] = salesperson.get_quotations_count()
        context['total_sales'] = salesperson.get_total_sales_amount()
        context['commission_earned'] = salesperson.get_commission_earned()
        
        # Cotizaciones recientes
        context['recent_quotations'] = salesperson.quotations.select_related('client').order_by('-created_at')[:10]
        
        # Estadísticas por estado
        context['quotation_stats'] = salesperson.quotations.aggregate(
            draft=Count('id', filter=Q(status='draft')),
            sent=Count('id', filter=Q(status='sent')),
            accepted=Count('id', filter=Q(status='accepted')),
            rejected=Count('id', filter=Q(status='rejected')),
            expired=Count('id', filter=Q(status='expired'))
        )
        
        return context

class SalesPersonCreateView(LoginRequiredMixin, CreateView):
    model = SalesPerson
    template_name = 'core/salesperson/form.html'
    fields = [
        'first_name', 'last_name', 'email', 'phone', 
        'employee_id', 'department', 'hire_date', 
        'commission_rate', 'notes'
    ]
    success_url = reverse_lazy('core:salesperson_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Vendedor creado exitosamente.')
        return super().form_valid(form)

class SalesPersonUpdateView(LoginRequiredMixin, UpdateView):
    model = SalesPerson
    template_name = 'core/salesperson/form.html'
    fields = [
        'first_name', 'last_name', 'email', 'phone', 
        'employee_id', 'department', 'hire_date', 
        'commission_rate', 'notes', 'is_active'
    ]
    success_url = reverse_lazy('core:salesperson_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Vendedor actualizado exitosamente.')
        return super().form_valid(form)

class SalesPersonDeleteView(LoginRequiredMixin, DeleteView):
    model = SalesPerson
    template_name = 'core/salesperson/delete.html'
    success_url = reverse_lazy('core:salesperson_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Vendedor eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

# Vistas para Perfil de Empresa
class CompanyProfileListView(LoginRequiredMixin, ListView):
    model = CompanyProfile
    template_name = 'core/company/list.html'
    context_object_name = 'profiles'
    ordering = ['-is_active', '-created_at']

class CompanyProfileDetailView(LoginRequiredMixin, DetailView):
    model = CompanyProfile
    template_name = 'core/company/detail.html'
    context_object_name = 'profile'

class CompanyProfileCreateView(LoginRequiredMixin, CreateView):
    model = CompanyProfile
    template_name = 'core/company/form.html'
    fields = [
        'name', 'address', 'phone', 'email', 'website',
        'facebook_url', 'instagram_url', 'tiktok_url', 'logo',
        'default_tax_rate', 'default_payment_terms', 'terms_and_conditions'
    ]
    success_url = reverse_lazy('core:company_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Perfil de empresa creado exitosamente.')
        return super().form_valid(form)

class CompanyProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CompanyProfile
    template_name = 'core/company/form.html'
    fields = [
        'name', 'address', 'phone', 'email', 'website',
        'facebook_url', 'instagram_url', 'tiktok_url', 'logo',
        'default_tax_rate', 'default_payment_terms', 'terms_and_conditions',
        'is_active'
    ]
    success_url = reverse_lazy('core:company_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Perfil de empresa actualizado exitosamente.')
        return super().form_valid(form)

class CompanyProfileDeleteView(LoginRequiredMixin, DeleteView):
    model = CompanyProfile
    template_name = 'core/company/delete.html'
    success_url = reverse_lazy('core:company_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Perfil de empresa eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

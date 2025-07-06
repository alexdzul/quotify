from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout
from django.views import View
from django.db.models import Count, Sum, Q, F
from django.db.models.functions import TruncMonth
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from apps.quotations.models import Quotation
from apps.clients.models import Client
from apps.services.models import Service
from .models import SalesPerson, CompanyProfile, SystemSettings

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
        context['total_companies'] = CompanyProfile.objects.count()
        context['total_salespersons'] = SalesPerson.objects.filter(is_active=True).count()
        
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
        accepted_value = Decimal('0.00')
        for quotation in Quotation.objects.all():
            total_value += quotation.total_amount
            if quotation.status == 'accepted':
                accepted_value += quotation.total_amount
        context['total_value'] = total_value
        context['accepted_value'] = accepted_value
        
        # Estadísticas por empresa
        companies_stats = []
        for company in CompanyProfile.objects.all():
            company_quotations = company.quotations.all()
            company_value = sum(q.total_amount for q in company_quotations)
            company_accepted = company_quotations.filter(status='accepted').count()
            companies_stats.append({
                'company': company,
                'quotations_count': company_quotations.count(),
                'total_value': company_value,
                'accepted_count': company_accepted,
                'conversion_rate': (company_accepted / company_quotations.count() * 100) if company_quotations.count() > 0 else 0
            })
        context['companies_stats'] = companies_stats
        
        # Estadísticas por vendedor
        salespersons_stats = []
        for salesperson in SalesPerson.objects.filter(is_active=True):
            sp_quotations = salesperson.quotations.all()
            sp_value = sum(q.total_amount for q in sp_quotations)
            sp_accepted = sp_quotations.filter(status='accepted').count()
            salespersons_stats.append({
                'salesperson': salesperson,
                'quotations_count': sp_quotations.count(),
                'total_value': sp_value,
                'accepted_count': sp_accepted,
                'conversion_rate': (sp_accepted / sp_quotations.count() * 100) if sp_quotations.count() > 0 else 0
            })
        # Ordenar por valor total descendente
        salespersons_stats.sort(key=lambda x: x['total_value'], reverse=True)
        context['salespersons_stats'] = salespersons_stats[:5]  # Top 5
        
        # Cotizaciones recientes
        context['recent_quotations'] = Quotation.objects.select_related('client', 'company_profile', 'salesperson').order_by('-created_at')[:5]
        
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
        'commission_rate', 'profile_photo', 'notes'
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
        'commission_rate', 'profile_photo', 'notes', 'is_active'
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
    ordering = ['name']
    paginate_by = 12
    
    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('quotations')
        
        # Búsqueda por nombre, email o dirección
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(address__icontains=search) |
                Q(website__icontains=search)
            )
        
        # Filtro por existencia de logo
        has_logo = self.request.GET.get('has_logo')
        if has_logo == 'yes':
            queryset = queryset.exclude(logo='')
        elif has_logo == 'no':
            queryset = queryset.filter(logo='')
        
        # Ordenamiento
        sort_by = self.request.GET.get('sort_by', 'name')
        if sort_by == 'quotations_count':
            # Ordenar por número de cotizaciones
            queryset = queryset.annotate(
                quotations_count=Count('quotations')
            ).order_by('-quotations_count')
        elif sort_by == 'created_at':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'updated_at':
            queryset = queryset.order_by('-updated_at')
        else:
            queryset = queryset.order_by('name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calcular estadísticas para cada perfil
        profiles_with_stats = []
        for profile in context['profiles']:
            quotations = profile.quotations.all()
            accepted_quotations = quotations.filter(status='accepted')
            
            profile_stats = {
                'profile': profile,
                'quotations_count': quotations.count(),
                'accepted_count': accepted_quotations.count(),
                'total_value': sum(q.total_amount for q in quotations),
                'accepted_value': sum(q.total_amount for q in accepted_quotations),
                'conversion_rate': (accepted_quotations.count() / quotations.count() * 100) if quotations.count() > 0 else 0,
                'recent_quotation_date': quotations.order_by('-created_at').first().created_at if quotations.exists() else None
            }
            profiles_with_stats.append(profile_stats)
        
        context['profiles_with_stats'] = profiles_with_stats
        
        # Parámetros de filtro actuales
        context['current_search'] = self.request.GET.get('search', '')
        context['current_has_logo'] = self.request.GET.get('has_logo', '')
        context['current_sort_by'] = self.request.GET.get('sort_by', 'name')
        
        # Estadísticas generales
        total_profiles = CompanyProfile.objects.count()
        profiles_with_logo = CompanyProfile.objects.exclude(logo='').count()
        profiles_with_quotations = CompanyProfile.objects.annotate(
            quotations_count=Count('quotations')
        ).filter(quotations_count__gt=0).count()
        
        context['general_stats'] = {
            'total_profiles': total_profiles,
            'profiles_with_logo': profiles_with_logo,
            'profiles_with_quotations': profiles_with_quotations,
            'profiles_without_quotations': total_profiles - profiles_with_quotations
        }
        
        return context

class CompanyProfileDetailView(LoginRequiredMixin, DetailView):
    model = CompanyProfile
    template_name = 'core/company/detail.html'
    context_object_name = 'profile'
    
    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'quotations__client',
            'quotations__salesperson'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        
        # Estadísticas del perfil de empresa
        quotations = profile.quotations.all()
        context['quotations_count'] = quotations.count()
        
        # Estadísticas por estado
        context['quotation_stats'] = quotations.aggregate(
            draft=Count('id', filter=Q(status='draft')),
            sent=Count('id', filter=Q(status='sent')),
            accepted=Count('id', filter=Q(status='accepted')),
            rejected=Count('id', filter=Q(status='rejected')),
            expired=Count('id', filter=Q(status='expired'))
        )
        
        # Valores financieros
        accepted_quotations = quotations.filter(status='accepted')
        context['total_value'] = sum(q.total_amount for q in quotations)
        context['accepted_value'] = sum(q.total_amount for q in accepted_quotations)
        context['pending_value'] = sum(q.total_amount for q in quotations.filter(status__in=['draft', 'sent']))
        
        # Tasa de conversión
        context['conversion_rate'] = (
            context['quotation_stats']['accepted'] / quotations.count() * 100
        ) if quotations.count() > 0 else 0
        
        # Cotizaciones recientes (últimas 10)
        context['recent_quotations'] = quotations.select_related(
            'client', 'salesperson'
        ).order_by('-created_at')[:10]
        
        # Fechas de primera y última cotización
        if quotations.exists():
            context['first_quotation_date'] = quotations.order_by('created_at').first().created_at
            context['last_quotation_date'] = quotations.order_by('-created_at').first().created_at
        else:
            context['first_quotation_date'] = None
            context['last_quotation_date'] = None
        
        # Top clientes por valor (solo si hay cotizaciones con items)
        if quotations.filter(items__isnull=False).exists():
            top_clients = quotations.values(
                'client__name', 'client__id'
            ).annotate(
                total_quoted=Sum(
                    F('items__quantity') * F('items__unit_price') * 
                    (1 + F('items__tax_rate') / 100)
                ),
                quotations_count=Count('id')
            ).filter(total_quoted__isnull=False).order_by('-total_quoted')[:5]
        else:
            top_clients = []
        context['top_clients'] = top_clients
        
        # Top vendedores (solo si hay cotizaciones con items)
        if quotations.filter(items__isnull=False).exists():
            top_salespersons = quotations.values(
                'salesperson__first_name', 
                'salesperson__last_name',
                'salesperson__id'
            ).annotate(
                total_quoted=Sum(
                    F('items__quantity') * F('items__unit_price') * 
                    (1 + F('items__tax_rate') / 100)
                ),
                quotations_count=Count('id')
            ).filter(total_quoted__isnull=False).order_by('-total_quoted')[:5]
        else:
            top_salespersons = []
        context['top_salespersons'] = top_salespersons
        
        # Actividad mensual (últimos 6 meses)
        from datetime import datetime, timedelta
        from django.utils import timezone
        from django.db.models.functions import TruncMonth
        
        six_months_ago = timezone.now() - timedelta(days=180)
        if quotations.filter(created_at__gte=six_months_ago).exists():
            monthly_activity = quotations.filter(
                created_at__gte=six_months_ago
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                count=Count('id'),
                total_value=Sum(
                    F('items__quantity') * F('items__unit_price') * 
                    (1 + F('items__tax_rate') / 100)
                )
            ).order_by('month')
        else:
            monthly_activity = []
        
        context['monthly_activity'] = monthly_activity
        
        return context

class CompanyProfileCreateView(LoginRequiredMixin, CreateView):
    model = CompanyProfile
    template_name = 'core/company/form.html'
    fields = [
        'name', 'slogan', 'address', 'phone', 'email', 'website',
        'facebook_url', 'instagram_url', 'tiktok_url', 'logo', 'cover_image',
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
        'name', 'slogan', 'address', 'phone', 'email', 'website',
        'facebook_url', 'instagram_url', 'tiktok_url', 'logo', 'cover_image',
        'default_tax_rate', 'default_payment_terms', 'terms_and_conditions'
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

# Vistas para Configuración del Sistema
class SystemSettingsUpdateView(LoginRequiredMixin, UpdateView):
    model = SystemSettings
    template_name = 'core/system_settings/form.html'
    fields = [
        'system_name', 'primary_color', 'quotation_validity_days', 
        'quotation_number_prefix', 'currency_symbol', 'currency_code',
        'default_email_from', 'enable_notifications'
    ]
    success_url = reverse_lazy('core:system_settings')
    
    def get_object(self, queryset=None):
        # Always get or create the single settings object
        return SystemSettings.get_settings()
    
    def form_valid(self, form):
        messages.success(self.request, 'Configuración del sistema actualizada exitosamente.')
        return super().form_valid(form)

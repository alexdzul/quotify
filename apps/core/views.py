from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View
from django.db.models import Count, Sum, Q
from apps.quotations.models import Quotation
from apps.clients.models import Client
from apps.services.models import Service
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

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django import forms
from .models import Quotation, QuotationItem
from apps.clients.models import Client
from apps.services.models import Service
import json

class QuotationListView(LoginRequiredMixin, ListView):
    model = Quotation
    template_name = 'quotations/list.html'
    context_object_name = 'quotations'
    paginate_by = 20
    ordering = ['-created_at']

class QuotationKanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'quotations/kanban.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Organizar cotizaciones por estado
        context['draft_quotations'] = Quotation.objects.filter(status='draft').select_related('client').order_by('-created_at')
        context['sent_quotations'] = Quotation.objects.filter(status='sent').select_related('client').order_by('-created_at')
        context['accepted_quotations'] = Quotation.objects.filter(status='accepted').select_related('client').order_by('-created_at')
        context['rejected_quotations'] = Quotation.objects.filter(status='rejected').select_related('client').order_by('-created_at')
        context['expired_quotations'] = Quotation.objects.filter(status='expired').select_related('client').order_by('-created_at')
        
        return context

class QuotationDetailView(LoginRequiredMixin, DetailView):
    model = Quotation
    template_name = 'quotations/detail.html'
    context_object_name = 'quotation'

class QuotationCreateView(LoginRequiredMixin, CreateView):
    model = Quotation
    template_name = 'quotations/form.html'
    fields = ['client', 'expiration_date', 'payment_terms', 'notes']
    success_url = reverse_lazy('quotations:list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Set widget for date field
        form.fields['expiration_date'].widget = forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = Client.objects.all().order_by('name')
        context['services'] = Service.objects.all().select_related('category').order_by('category__name', 'name')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Cotización creada exitosamente.')
        return super().form_valid(form)

class QuotationUpdateView(LoginRequiredMixin, UpdateView):
    model = Quotation
    template_name = 'quotations/form.html'
    fields = ['client', 'expiration_date', 'payment_terms', 'notes', 'status']
    success_url = reverse_lazy('quotations:list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Set widget for date field
        form.fields['expiration_date'].widget = forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = Client.objects.all().order_by('name')
        context['services'] = Service.objects.all().select_related('category').order_by('category__name', 'name')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Cotización actualizada exitosamente.')
        return super().form_valid(form)

class QuotationDeleteView(LoginRequiredMixin, DeleteView):
    model = Quotation
    template_name = 'quotations/delete.html'
    success_url = reverse_lazy('quotations:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Cotización eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

class QuotationDuplicateView(LoginRequiredMixin, DetailView):
    model = Quotation
    
    def get(self, request, *args, **kwargs):
        original = self.get_object()
        
        # Crear copia de la cotización
        new_quotation = Quotation.objects.create(
            client=original.client,
            payment_terms=original.payment_terms,
            notes=f"Copia de: {original.notes}" if original.notes else "Copia de cotización",
            status='draft'
        )
        
        # Copiar items
        for item in original.items.all():
            QuotationItem.objects.create(
                quotation=new_quotation,
                service=item.service,
                quantity=item.quantity,
                unit_price=item.unit_price,
                description=item.description
            )
        
        messages.success(request, f'Cotización duplicada como {new_quotation.quotation_number}')
        return redirect('quotations:update', pk=new_quotation.pk)

@login_required
@require_POST
@csrf_exempt
def update_quotation_status(request, pk):
    """Vista AJAX para actualizar el estado de una cotización desde Kanban"""
    try:
        quotation = get_object_or_404(Quotation, pk=pk)
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status in ['draft', 'sent', 'accepted', 'rejected', 'expired']:
            quotation.status = new_status
            quotation.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Estado actualizado a {quotation.get_status_display()}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Estado inválido'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

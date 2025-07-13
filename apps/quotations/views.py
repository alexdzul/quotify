from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django import forms
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import tempfile
import os
from .models import Quotation, QuotationItem, QuotationActivity, QuotationPhotographicReport
from apps.clients.models import Client
from apps.services.models import Service
from apps.core.models import CompanyProfile, SalesPerson
import json
import traceback
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

class QuotationListView(LoginRequiredMixin, ListView):
    model = Quotation
    template_name = 'quotations/list.html'
    context_object_name = 'quotations'
    paginate_by = 20
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('client', 'company_profile', 'salesperson')
        
        # Filtro por empresa
        company_profile_id = self.request.GET.get('company_profile')
        if company_profile_id:
            queryset = queryset.filter(company_profile_id=company_profile_id)
        
        # Filtro por cliente
        client_id = self.request.GET.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filtro por vendedor
        salesperson_id = self.request.GET.get('salesperson')
        if salesperson_id:
            queryset = queryset.filter(salesperson_id=salesperson_id)
        
        # Filtro por estado
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Búsqueda por texto (número de cotización o nombre de cliente)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(quotation_number__icontains=search) |
                Q(client__name__icontains=search) |
                Q(notes__icontains=search) |
                Q(company_profile__name__icontains=search) |
                Q(salesperson__first_name__icontains=search) |
                Q(salesperson__last_name__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar listas para los filtros
        context['clients'] = Client.objects.all().order_by('name')
        context['company_profiles'] = CompanyProfile.objects.all().order_by('name')
        context['salespersons'] = SalesPerson.objects.all().order_by('first_name', 'last_name')
        context['status_choices'] = Quotation.STATUS_CHOICES
        
        # Mantener los valores de filtro actuales en el contexto
        context['current_client'] = self.request.GET.get('client')
        context['current_company_profile'] = self.request.GET.get('company_profile')
        context['current_salesperson'] = self.request.GET.get('salesperson')
        context['current_status'] = self.request.GET.get('status')
        context['current_search'] = self.request.GET.get('search', '')
        
        # Agregar objetos actuales para mostrar en los filtros activos
        if context['current_client']:
            try:
                context['current_client_obj'] = Client.objects.get(id=context['current_client'])
            except Client.DoesNotExist:
                context['current_client_obj'] = None
        
        if context['current_company_profile']:
            try:
                context['current_company_profile_obj'] = CompanyProfile.objects.get(id=context['current_company_profile'])
            except CompanyProfile.DoesNotExist:
                context['current_company_profile_obj'] = None
        
        if context['current_salesperson']:
            try:
                context['current_salesperson_obj'] = SalesPerson.objects.get(id=context['current_salesperson'])
            except SalesPerson.DoesNotExist:
                context['current_salesperson_obj'] = None
        
        if context['current_status']:
            context['current_status_display'] = dict(Quotation.STATUS_CHOICES).get(context['current_status'])
        
        return context

class QuotationKanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'quotations/kanban.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtrar por empresa si se especifica
        company_profile_id = self.request.GET.get('company_profile')
        base_queryset = Quotation.objects.select_related('client', 'company_profile')
        
        if company_profile_id:
            base_queryset = base_queryset.filter(company_profile_id=company_profile_id)
        
        # Organizar cotizaciones por estado (excluyendo expiradas que se manejan automáticamente)
        context['draft_quotations'] = base_queryset.filter(status='draft').order_by('-created_at')
        context['sent_quotations'] = base_queryset.filter(status='sent').order_by('-created_at')
        context['accepted_quotations'] = base_queryset.filter(status='accepted').order_by('-created_at')
        context['rejected_quotations'] = base_queryset.filter(status='rejected').order_by('-created_at')
        
        # Agregar perfiles de empresa para el filtro
        context['company_profiles'] = CompanyProfile.objects.all().order_by('name')
        context['current_company_profile'] = company_profile_id
        if company_profile_id:
            try:
                context['current_company_profile_obj'] = CompanyProfile.objects.get(id=company_profile_id)
            except CompanyProfile.DoesNotExist:
                context['current_company_profile_obj'] = None
        return context

class QuotationDetailView(LoginRequiredMixin, DetailView):
    model = Quotation
    template_name = 'quotations/detail.html'
    context_object_name = 'quotation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar historial de actividades
        context['activities'] = self.object.activities.all().order_by('-created_at')[:20]
        return context

class QuotationCreateView(LoginRequiredMixin, CreateView):
    model = Quotation
    template_name = 'quotations/form.html'
    fields = ['company_profile', 'client', 'salesperson', 'expiration_date', 'payment_terms', 'notes']
    
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
        context['salespersons'] = SalesPerson.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        # Agregar información sobre elementos preseleccionados para mostrar en la UI
        preselected_info = {}
        
        company_profile_id = self.request.GET.get('company_profile')
        if company_profile_id:
            try:
                company_profile = CompanyProfile.objects.get(id=company_profile_id)
                preselected_info['company_profile'] = company_profile
            except (CompanyProfile.DoesNotExist, ValueError):
                pass
        
        client_id = self.request.GET.get('client')
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                preselected_info['client'] = client
            except (Client.DoesNotExist, ValueError):
                pass
        
        salesperson_id = self.request.GET.get('salesperson')
        if salesperson_id:
            try:
                salesperson = SalesPerson.objects.get(id=salesperson_id, is_active=True)
                preselected_info['salesperson'] = salesperson
            except (SalesPerson.DoesNotExist, ValueError):
                pass
        
        context['preselected_info'] = preselected_info
        return context
    
    def get_initial(self):
        initial = super().get_initial()
        
        # Preseleccionar perfil de empresa desde query params
        company_profile_id = self.request.GET.get('company_profile')
        if company_profile_id:
            try:
                company_profile = CompanyProfile.objects.get(id=company_profile_id)
                initial['company_profile'] = company_profile
            except (CompanyProfile.DoesNotExist, ValueError):
                pass  # Si no existe o ID inválido, continuar sin preselección
        else:
            # Pre-seleccionar el primer perfil disponible por defecto si no se especifica uno
            first_profile = CompanyProfile.objects.first()
            if first_profile:
                initial['company_profile'] = first_profile
        
        # Preseleccionar cliente desde query params
        client_id = self.request.GET.get('client')
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                initial['client'] = client
            except (Client.DoesNotExist, ValueError):
                pass  # Si no existe o ID inválido, continuar sin preselección
        
        # Preseleccionar vendedor desde query params
        salesperson_id = self.request.GET.get('salesperson')
        if salesperson_id:
            try:
                salesperson = SalesPerson.objects.get(id=salesperson_id, is_active=True)
                initial['salesperson'] = salesperson
            except (SalesPerson.DoesNotExist, ValueError):
                pass  # Si no existe o ID inválido, continuar sin preselección
        
        # Preseleccionar términos de pago desde el perfil de empresa
        company_profile = initial.get('company_profile')
        if company_profile and company_profile.default_payment_terms:
            initial['payment_terms'] = company_profile.default_payment_terms
        else:
            # Valor por defecto si no hay perfil de empresa
            initial['payment_terms'] = "Anticipo del 60% para la programación de los trabajos.\nSaldo del 40% al término de los mismos."
        
        return initial
    
    def form_valid(self, form):
        print("=== FORMULARIO VÁLIDO ===")
        print(f"Form cleaned_data: {form.cleaned_data}")
        try:
            result = super().form_valid(form)
            print(f"Cotización creada exitosamente: {self.object}")
            messages.success(self.request, 'Cotización creada exitosamente.')
            return result
        except Exception as e:
            print(f"Error al guardar: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            messages.error(self.request, f'Error al guardar: {e}')
            return self.render_to_response(self.get_context_data(form=form))
    
    def form_invalid(self, form):
        # Log detallado para debugging
        print("=== ERRORES DEL FORMULARIO ===")
        print(f"Form errors: {form.errors}")
        print(f"Form data: {form.data}")
        print(f"Form cleaned_data: {getattr(form, 'cleaned_data', 'No cleaned_data available')}")
        
        # Agregar mensajes de error para debugging
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Error en {field}: {error}")
        
        # Si hay errores no relacionados a campos específicos
        if form.non_field_errors():
            for error in form.non_field_errors():
                messages.error(self.request, f"Error: {error}")
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('quotations:detail', kwargs={'pk': self.object.pk})

class QuotationUpdateView(LoginRequiredMixin, UpdateView):
    model = Quotation
    template_name = 'quotations/form.html'
    fields = ['company_profile', 'client', 'salesperson', 'expiration_date', 'payment_terms', 'notes', 'status']
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
        context['salespersons'] = SalesPerson.objects.filter(is_active=True).order_by('first_name', 'last_name')
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Cotización actualizada exitosamente.')
        return super().form_valid(form)

class QuotationDeleteView(LoginRequiredMixin, DeleteView):
    model = Quotation
    template_name = 'quotations/delete.html'
    success_url = reverse_lazy('quotations:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quotation = self.object
        
        # Verificar si se puede eliminar
        can_delete = quotation.status in ['draft', 'rejected', 'expired']
        context['can_delete'] = can_delete
        
        if not can_delete:
            if quotation.status == 'accepted':
                context['delete_restriction_message'] = 'No se puede eliminar una cotización aceptada. Considere crear una nueva cotización en su lugar.'
            elif quotation.status == 'sent':
                context['delete_restriction_message'] = 'No se puede eliminar una cotización que ya ha sido enviada al cliente. Primero cambie el estado a "Borrador" o "Rechazada".'
        
        return context
    
    def dispatch(self, request, *args, **kwargs):
        quotation = self.get_object()
        
        # Solo permitir eliminación para ciertos estados
        if quotation.status not in ['draft', 'rejected', 'expired']:
            messages.error(
                request, 
                f'No se puede eliminar una cotización con estado "{quotation.get_status_display()}". '
                'Solo se pueden eliminar cotizaciones en estado Borrador, Rechazada o Expirada.'
            )
            return redirect('quotations:detail', pk=quotation.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        quotation = self.get_object()
        
        # Registrar actividad antes de eliminar
        QuotationActivity.objects.create(
            quotation=quotation,
            activity_type='status_change',
            title='Cotización eliminada',
            description=f'La cotización {quotation.quotation_number} fue eliminada por el usuario {request.user.get_full_name() or request.user.username}',
            user=request.user,
            is_automatic=True
        )
        
        messages.success(
            self.request, 
            f'Cotización {quotation.quotation_number} eliminada exitosamente.'
        )
        return super().delete(request, *args, **kwargs)

class QuotationDuplicateView(LoginRequiredMixin, DetailView):
    model = Quotation
    
    def get(self, request, *args, **kwargs):
        original = self.get_object()
        
        # Crear copia de la cotización
        new_quotation = Quotation.objects.create(
            company_profile=original.company_profile,
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
            old_status = quotation.status
            quotation.status = new_status
            quotation.save()
            
            # Registrar actividad automática de cambio de estado
            from .models import QuotationActivity
            QuotationActivity.create_status_change_activity(
                quotation=quotation,
                old_status=old_status,
                new_status=new_status,
                user=request.user
            )
            
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


# Vistas para Activities (CRM-like functionality)
from .models import QuotationActivity

class QuotationActivityCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear actividades manuales en cotizaciones"""
    model = QuotationActivity
    template_name = 'quotations/activity/form.html'
    fields = [
        'activity_type', 'title', 'description', 
        'scheduled_date', 'priority', 'requires_follow_up', 'follow_up_date',
        'contact_person', 'contact_email', 'contact_phone'
    ]
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Set widgets for date fields
        form.fields['scheduled_date'].widget = forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
        form.fields['follow_up_date'].widget = forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
        
        # Set form classes
        for field_name, field in form.fields.items():
            if field_name not in ['requires_follow_up']:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'
        
        return form
    
    def form_valid(self, form):
        # Obtener la cotización desde URL
        quotation_pk = self.kwargs.get('quotation_pk')
        quotation = get_object_or_404(Quotation, pk=quotation_pk)
        
        form.instance.quotation = quotation
        form.instance.user = self.request.user
        form.instance.is_automatic = False
        
        messages.success(self.request, 'Actividad registrada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('quotations:detail', kwargs={'pk': self.object.quotation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quotation_pk = self.kwargs.get('quotation_pk')
        context['quotation'] = get_object_or_404(Quotation, pk=quotation_pk)
        return context


class QuotationActivityListView(LoginRequiredMixin, ListView):
    """Vista para listar todas las actividades de una cotización"""
    model = QuotationActivity
    template_name = 'quotations/activity/list.html'
    context_object_name = 'activities'
    paginate_by = 20
    
    def get_queryset(self):
        quotation_pk = self.kwargs.get('quotation_pk')
        return QuotationActivity.objects.filter(
            quotation__pk=quotation_pk
        ).select_related('user', 'quotation').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quotation_pk = self.kwargs.get('quotation_pk')
        context['quotation'] = get_object_or_404(Quotation, pk=quotation_pk)
        
        # Filtros
        activity_type = self.request.GET.get('type')
        if activity_type:
            context['activities'] = context['activities'].filter(activity_type=activity_type)
        
        # Estadísticas rápidas
        queryset = self.get_queryset()
        context['stats'] = {
            'total': queryset.count(),
            'completed': queryset.filter(completed_date__isnull=False).count(),
            'overdue': sum(1 for activity in queryset if activity.is_overdue),
            'follow_up': queryset.filter(requires_follow_up=True, follow_up_date__isnull=False).count()
        }
        
        return context


class QuotationActivityUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar actividades"""
    model = QuotationActivity
    template_name = 'quotations/activity/form.html'
    fields = [
        'activity_type', 'title', 'description', 
        'scheduled_date', 'completed_date', 'priority', 
        'requires_follow_up', 'follow_up_date',
        'contact_person', 'contact_email', 'contact_phone'
    ]
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Set widgets for date fields
        form.fields['scheduled_date'].widget = forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
        form.fields['completed_date'].widget = forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
        form.fields['follow_up_date'].widget = forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
        
        # Set form classes
        for field_name, field in form.fields.items():
            if field_name not in ['requires_follow_up']:
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'
        
        return form
    
    def form_valid(self, form):
        messages.success(self.request, 'Actividad actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('quotations:detail', kwargs={'pk': self.object.quotation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quotation'] = self.object.quotation
        return context


@login_required
@require_POST
def mark_activity_completed(request, pk):
    """Vista AJAX para marcar una actividad como completada"""
    try:
        activity = get_object_or_404(QuotationActivity, pk=pk)
        activity.mark_completed()
        
        return JsonResponse({
            'success': True,
            'message': 'Actividad marcada como completada'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# Vistas para manejar Items de Cotización
class QuotationItemCreateView(LoginRequiredMixin, CreateView):
    """Vista para agregar items a una cotización"""
    model = QuotationItem
    template_name = 'quotations/item/form.html'
    fields = ['service', 'quantity', 'unit_price', 'tax_rate', 'description', 'custom_image']
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Aplicar clases CSS
        for field_name, field in form.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Widget especial para el campo de servicio
        form.fields['service'].widget.attrs.update({
            'class': 'form-control',
            'onchange': 'updateServiceInfo(this.value)'
        })
        
        # Solo mostrar servicios activos
        form.fields['service'].queryset = Service.objects.filter(is_active=True).select_related('category')
        
        return form
    
    def form_valid(self, form):
        # Obtener la cotización desde URL
        quotation_pk = self.kwargs.get('quotation_pk')
        quotation = get_object_or_404(Quotation, pk=quotation_pk)
        
        form.instance.quotation = quotation
        
        # Registrar actividad automática
        QuotationActivity.objects.create(
            quotation=quotation,
            activity_type='item_added',
            title=f'Servicio agregado: {form.instance.service.name}',
            description=f'Se agregó el servicio "{form.instance.service.name}" (Cantidad: {form.instance.quantity}) a la cotización',
            user=self.request.user,
            is_automatic=True
        )
        
        messages.success(self.request, f'Servicio "{form.instance.service.name}" agregado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('quotations:detail', kwargs={'pk': self.object.quotation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quotation_pk = self.kwargs.get('quotation_pk')
        context['quotation'] = get_object_or_404(Quotation, pk=quotation_pk)
        context['services'] = Service.objects.filter(is_active=True).select_related('category').order_by('category__name', 'name')
        return context


class QuotationItemUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar items de una cotización"""
    model = QuotationItem
    template_name = 'quotations/item/form.html'
    fields = ['service', 'quantity', 'unit_price', 'tax_rate', 'description', 'custom_image']
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Aplicar clases CSS
        for field_name, field in form.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Widget especial para el campo de servicio
        form.fields['service'].widget.attrs.update({
            'class': 'form-control',
            'onchange': 'updateServiceInfo(this.value)'
        })
        
        # Solo mostrar servicios activos
        form.fields['service'].queryset = Service.objects.filter(is_active=True).select_related('category')
        
        return form
    
    def form_valid(self, form):
        # Registrar actividad automática
        QuotationActivity.objects.create(
            quotation=self.object.quotation,
            activity_type='item_updated',
            title=f'Servicio actualizado: {form.instance.service.name}',
            description=f'Se actualizó el servicio "{form.instance.service.name}" en la cotización',
            user=self.request.user,
            is_automatic=True
        )
        
        messages.success(self.request, f'Servicio "{form.instance.service.name}" actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('quotations:detail', kwargs={'pk': self.object.quotation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['quotation'] = self.object.quotation
        context['services'] = Service.objects.filter(is_active=True).select_related('category').order_by('category__name', 'name')
        return context


class QuotationItemDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar items de una cotización"""
    model = QuotationItem
    template_name = 'quotations/item/delete.html'
    
    def delete(self, request, *args, **kwargs):
        item = self.get_object()
        service_name = item.service.name
        quotation = item.quotation
        
        # Registrar actividad automática antes de eliminar
        QuotationActivity.objects.create(
            quotation=quotation,
            activity_type='item_removed',
            title=f'Servicio eliminado: {service_name}',
            description=f'Se eliminó el servicio "{service_name}" de la cotización',
            user=request.user,
            is_automatic=True
        )
        
        messages.success(request, f'Servicio "{service_name}" eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('quotations:detail', kwargs={'pk': self.object.quotation.pk})


@login_required
def get_company_info(request, company_id):
    """Vista AJAX para obtener información de una empresa"""
    try:
        company = get_object_or_404(CompanyProfile, id=company_id)
        return JsonResponse({
            'success': True,
            'default_payment_terms': company.default_payment_terms,
            'default_tax_rate': float(company.default_tax_rate),
            'terms_and_conditions': company.terms_and_conditions,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
@csrf_exempt
def get_service_info(request):
    """Vista AJAX para obtener información de un servicio"""
    try:
        service_id = request.POST.get('service_id') or request.GET.get('service_id')
        service = get_object_or_404(Service, pk=service_id)
        
        return JsonResponse({
            'success': True,
            'service': {
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'unit_price': str(service.unit_price),
                'tax_rate': str(service.tax_rate),
                'unit': service.unit,
                'unit_display': service.get_unit_display(),
                'category': service.category.name if service.category else '',
                'image_url': service.main_image.url if service.main_image else ''
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
@csrf_exempt
def add_item_quick(request, quotation_pk):
    """Vista AJAX para agregar items rápidamente"""
    try:
        quotation = get_object_or_404(Quotation, pk=quotation_pk)
        data = json.loads(request.body)
        
        service_id = data.get('service_id')
        quantity = data.get('quantity', 1)
        
        service = get_object_or_404(Service, pk=service_id)
        
        # Crear el item
        item = QuotationItem.objects.create(
            quotation=quotation,
            service=service,
            quantity=quantity,
            unit_price=service.unit_price,
            tax_rate=service.tax_rate
        )
        
        # Registrar actividad automática
        QuotationActivity.objects.create(
            quotation=quotation,
            activity_type='item_added',
            title=f'Servicio agregado: {service.name}',
            description=f'Se agregó rápidamente el servicio "{service.name}" (Cantidad: {quantity}) a la cotización',
            user=request.user,
            is_automatic=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Servicio "{service.name}" agregado exitosamente',
            'item': {
                'id': item.id,
                'service_name': service.name,
                'quantity': str(item.quantity),
                'unit_price': str(item.unit_price),
                'subtotal': str(item.subtotal),
                'tax_amount': str(item.tax_amount),
                'total_amount': str(item.total_amount)
            },
            'quotation_totals': {
                'subtotal': str(quotation.subtotal),
                'tax_amount': str(quotation.tax_amount),
                'total_amount': str(quotation.total_amount)
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


class QuotationPDFView(LoginRequiredMixin, DetailView):
    """Vista para generar PDF de la cotización"""
    model = Quotation
    
    def get(self, request, *args, **kwargs):
        quotation = self.get_object()
        company_profile = quotation.company_profile
        
        # Construir URLs absolutas para las imágenes
        items_with_absolute_urls = []
        for item in quotation.items.all().select_related('service', 'service__category'):
            item_data = {
                'item': item,
                'display_image_url': request.build_absolute_uri(item.display_image.url) if item.display_image else None,
                'service_images': []
            }
            
            # Agregar URLs absolutas para todas las imágenes de la galería del servicio
            for img in item.service.gallery_images.all():
                item_data['service_images'].append({
                    'url': request.build_absolute_uri(img.image.url),
                    'caption': img.caption or 'Imagen del servicio'
                })
            
            items_with_absolute_urls.append(item_data)
        
        # Preparar las imágenes de evidencia fotográfica con URLs absolutas
        photographic_report_with_urls = []
        for photo in quotation.photographic_report.all().order_by('photo_type', 'order'):
            photo_data = {
                'photo': photo,
                'display_title': photo.display_title,
                'get_photo_type_display': photo.get_photo_type_display(),
                'location_description': photo.location_description,
                'photo_date': photo.photo_date,
                'description': photo.description,
                'image_url': request.build_absolute_uri(photo.image.url) if photo.image else None,
            }
            photographic_report_with_urls.append(photo_data)
        
        # Preparar el contexto para el PDF
        context = {
            'quotation': quotation,
            'company_profile': company_profile,
            'company_logo_url': request.build_absolute_uri(company_profile.logo.url) if company_profile and company_profile.logo else None,
            'company_cover_image_url': request.build_absolute_uri(company_profile.cover_image.url) if company_profile and company_profile.cover_image else None,
            'company_slogan': company_profile.slogan if company_profile and company_profile.slogan else "NUESTRO COMPROMISO: SU JARDÍN",
            'company_brand_color': company_profile.brand_color if company_profile and company_profile.brand_color else "#2c5f2d",
            'salesperson_photo_url': request.build_absolute_uri(quotation.salesperson.profile_photo.url) if quotation.salesperson and quotation.salesperson.profile_photo else None,
            'items_with_urls': items_with_absolute_urls,
            'photographic_report': photographic_report_with_urls,
        }
        
        # Renderizar el HTML
        html_string = render_to_string('quotations/pdf_template.html', context, request=request)
        
        # Configurar WeasyPrint
        font_config = FontConfiguration()
        
        # Función para generar colores más claros y oscuros
        def lighten_color(hex_color, amount=0.3):
            """Hace un color más claro"""
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = min(255, int(r + (255 - r) * amount))
            g = min(255, int(g + (255 - g) * amount))
            b = min(255, int(b + (255 - b) * amount))
            return f"#{r:02x}{g:02x}{b:02x}"
        
        def darken_color(hex_color, amount=0.2):
            """Hace un color más oscuro"""
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = max(0, int(r * (1 - amount)))
            g = max(0, int(g * (1 - amount)))
            b = max(0, int(b * (1 - amount)))
            return f"#{r:02x}{g:02x}{b:02x}"
        
        # Generar colores basados en el color de la empresa
        brand_color = context['company_brand_color']
        brand_light = lighten_color(brand_color, 0.5)
        brand_dark = darken_color(brand_color, 0.1)
        
        # CSS dinámico para el PDF
        css_string = f"""
        @page {{
            size: A4;
            margin: 0;
        }}
        
        body {{
            font-family: 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }}
        
        /* ESTILOS PARA LA PORTADA */
        .cover-page {{
            width: 100%;
            height: 297mm;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            position: relative;
            display: flex;
            flex-direction: column;
            page-break-after: always;
        }}
        
        .cover-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 30px 40px;
            height: 120px;
        }}
        
        .cover-logo img {{
            max-height: 80px;
            max-width: 200px;
        }}
        
        .cover-date {{
            background: #F5E6A3;
            padding: 15px 25px;
            border-radius: 0 0 0 15px;
            text-align: center;
            min-width: 100px;
        }}
        
        .date-month {{
            font-size: 18px;
            font-weight: bold;
            color: {brand_color};
            margin-bottom: 5px;
        }}
        
        .date-year {{
            font-size: 24px;
            font-weight: bold;
            color: {brand_color};
        }}
        
        .cover-title {{
            text-align: center;
            margin: 40px 0 20px 0;
            background: #e9ecef;
            padding: 40px;
            border-radius: 15px;
            margin-left: 40px;
            margin-right: 40px;
        }}
        
        .cover-title h1 {{
            font-size: 42px;
            color: #333;
            margin: 0;
            font-weight: normal;
        }}
        
        .quote-number {{
            font-weight: bold;
            color: {brand_color};
        }}
        
        .cover-subtitle {{
            font-size: 22px;
            color: #8B4513;
            margin-top: 15px;
            font-weight: 500;
        }}
        
        .commitment-banner {{
            background: #F5E6A3;
            padding: 15px 0;
            margin: 30px 0;
            text-align: center;
            width: 100%;
        }}
        
        .commitment-text {{
            font-size: 18px;
            font-weight: bold;
            color: {brand_color};
            letter-spacing: 1px;
        }}
        
        .cover-image {{
            flex-grow: 1;
            margin: 0 40px;
            margin-bottom: 80px;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .cover-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .default-image {{
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, {brand_color} 0%, {brand_dark} 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            text-align: center;
        }}
        
        .default-content h2 {{
            font-size: 32px;
            margin: 0 0 10px 0;
        }}
        
        .default-content p {{
            font-size: 18px;
            margin: 0;
        }}
        
        .cover-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 40px;
            background: rgba(255, 255, 255, 0.8);
            margin-top: auto;
        }}
        
        .website {{
            font-size: 16px;
            color: {brand_color};
            font-weight: bold;
        }}
        
        .store-info {{
            font-size: 14px;
            color: #666;
            background: #f8f9fa;
            padding: 5px 10px;
            border-radius: 10px;
        }}
        
        /* SALTO DE PÁGINA */
        .page-break {{
            page-break-before: always;
        }}
        
        /* ESTILOS PARA CONTENIDO INTERNO */
        .company-info,
        .quotation-info,
        .service-section,
        .totals-section,
        .terms-section,
        .items-table,
        h2 {{
            margin-left: 20px;
            margin-right: 20px;
        }}
        
        .company-info {{
            background: linear-gradient(135deg, {brand_color}, {brand_dark});
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            margin-top: 20px;
        }}
        
        .quotation-info {{
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid {brand_color};
            margin-bottom: 25px;
        }}
        
        .client-info {{
            background: #fff;
            border: 1px solid #dee2e6;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 25px;
        }}
        
        .service-section {{
            margin-bottom: 40px;
            page-break-inside: avoid;
        }}
        
        .service-header {{
            background: {brand_color};
            color: white;
            padding: 15px;
            margin-bottom: 15px;
        }}
        
        .service-content {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .service-image {{
            flex: 0 0 200px;
        }}
        
        .service-image img {{
            width: 100%;
            height: 150px;
            object-fit: cover;
            border-radius: 5px;
        }}
        
        .service-description {{
            flex: 1;
        }}
        
        .service-gallery {{
            margin: 15px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }}
        
        .service-gallery h5 {{
            color: {brand_color};
            margin-bottom: 10px;
            font-size: 14px;
            font-weight: bold;
        }}
        
        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 8px;
        }}
        
        .gallery-item {{
            text-align: center;
        }}
        
        .gallery-item img {{
            width: 100%;
            height: 90px;
            object-fit: cover;
            border-radius: 4px;
            border: 1px solid #dee2e6;
        }}
        
        .gallery-item .caption {{
            font-size: 10px;
            color: #666;
            margin-top: 3px;
            font-style: italic;
        }}
        
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        
        .items-table th,
        .items-table td {{
            border: 1px solid #dee2e6;
            padding: 12px;
            text-align: left;
        }}
        
        .items-table th {{
            background: {brand_color};
            color: white;
            font-weight: bold;
        }}
        
        .items-table tbody tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        .totals-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        
        .totals-table {{
            width: 300px;
            margin-left: auto;
        }}
        
        .totals-table td {{
            padding: 8px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .total-final {{
            font-weight: bold;
            font-size: 1.2em;
            background: {brand_color};
            color: white;
        }}
        
        .terms-section {{
            page-break-before: always;
            margin-bottom: 30px;
        }}
        
        .terms-section h2 {{
            color: {brand_color};
            border-bottom: 2px solid {brand_color};
            padding-bottom: 10px;
        }}
        
        .terms-content {{
            background: #fff;
            padding: 20px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            white-space: pre-line;
        }}
        
        .social-footer {{
            page-break-before: always;
            text-align: center;
            background: linear-gradient(135deg, {brand_color}, {brand_dark});
            color: white;
            padding: 40px;
            border-radius: 10px;
        }}
        
        .social-links {{
            margin-top: 20px;
        }}
        
        .social-links a {{
            color: white;
            text-decoration: none;
            margin: 0 10px;
            font-weight: bold;
        }}
        
        /* Estilos para Evidencia Fotográfica */
        .photographic-evidence {{
            margin-bottom: 30px;
            page-break-inside: avoid;
        }}
        
        .photographic-evidence h2 {{
            color: {brand_color};
            border-bottom: 2px solid {brand_color};
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        .evidence-gallery {{
            margin-top: 15px;
        }}
        
        .evidence-item {{
            margin-bottom: 25px;
            padding: 15px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            background: #f8f9fa;
            page-break-inside: avoid;
        }}
        
        .evidence-header h4 {{
            color: {brand_color};
            margin: 0 0 10px 0;
            font-size: 16px;
        }}
        
        .evidence-image {{
            text-align: center;
            margin: 15px 0;
        }}
        
        .evidence-image img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .evidence-description {{
            margin-top: 10px;
            font-size: 14px;
            color: #555;
            background: #fff;
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid {brand_color};
        }}
        
        .text-right {{
            text-align: right;
        }}
        
        .text-center {{
            text-align: center;
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        """
        
        # Crear el PDF
        html = HTML(string=html_string)
        css = CSS(string=css_string, font_config=font_config)
        
        # Generar el PDF
        pdf_file = html.write_pdf(stylesheets=[css], font_config=font_config)
        
        # Crear la respuesta HTTP
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Cotizacion_{quotation.quotation_number}.pdf"'
        
        return response


class QuotationPreviewView(LoginRequiredMixin, DetailView):
    """Vista para previsualizar la cotización en HTML antes de generar PDF"""
    model = Quotation
    template_name = 'quotations/pdf_preview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quotation = self.get_object()
        company_profile = quotation.company_profile
        
        # Construir URLs para las imágenes (para web no necesitamos URLs absolutas)
        items_with_urls = []
        for item in quotation.items.all().select_related('service', 'service__category'):
            item_data = {
                'item': item,
                'display_image_url': item.display_image.url if item.display_image else None,
                'service_images': []
            }
            
            # Agregar todas las imágenes de la galería del servicio
            for img in item.service.gallery_images.all():
                item_data['service_images'].append({
                    'url': img.image.url,
                    'caption': img.caption or 'Imagen del servicio'
                })
            
            items_with_urls.append(item_data)
        
        context.update({
            'company_profile': company_profile,
            'company_logo_url': company_profile.logo.url if company_profile and company_profile.logo else None,
            'company_cover_image_url': company_profile.cover_image.url if company_profile and company_profile.cover_image else None,
            'company_slogan': company_profile.slogan if company_profile and company_profile.slogan else "NUESTRO COMPROMISO: SU JARDÍN",
            'company_brand_color': company_profile.brand_color if company_profile and company_profile.brand_color else "#2c5f2d",
            'salesperson_photo_url': quotation.salesperson.profile_photo.url if quotation.salesperson and quotation.salesperson.profile_photo else None,
            'items_with_urls': items_with_urls,
            'photographic_report': quotation.photographic_report.all().order_by('photo_type', 'order'),
            'is_preview': True,  # Flag para indicar que es preview
        })
        
        return context


@login_required
@require_POST
def photo_upload(request, quotation_pk):
    """Vista AJAX para subir fotos de evidencia fotográfica"""
    try:
        quotation = get_object_or_404(Quotation, pk=quotation_pk)
        photos = request.FILES.getlist('photos')
        
        if not photos:
            return JsonResponse({'success': False, 'error': 'No se seleccionaron fotos'})
        
        photo_type = request.POST.get('photo_type', 'before')
        location_description = request.POST.get('location_description', '')
        description = request.POST.get('description', '')
        
        uploaded_photos = []
        
        for i, photo_file in enumerate(photos):
            # Crear título automático si no hay descripción específica
            if description:
                title = f"{description} - Foto {i+1}"
            else:
                title = f"Evidencia fotográfica - Foto {i+1}"
            
            # Crear el objeto QuotationPhotographicReport
            photo_report = QuotationPhotographicReport.objects.create(
                quotation=quotation,
                image=photo_file,
                photo_type=photo_type,
                title=title,
                description=description,
                location_description=location_description,
                order=quotation.photographic_report.count() + i + 1
            )
            
            uploaded_photos.append({
                'id': photo_report.pk,
                'title': photo_report.display_title,
                'image_url': photo_report.image.url,
                'photo_type': photo_report.get_photo_type_display()
            })
        
        return JsonResponse({
            'success': True, 
            'message': f'{len(uploaded_photos)} foto(s) subida(s) exitosamente',
            'photos': uploaded_photos
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def photo_detail(request, quotation_pk, photo_pk):
    """Vista AJAX para obtener detalles de una foto"""
    try:
        quotation = get_object_or_404(Quotation, pk=quotation_pk)
        photo = get_object_or_404(QuotationPhotographicReport, pk=photo_pk, quotation=quotation)
        
        data = {
            'title': photo.display_title,
            'image_url': photo.image.url,
            'photo_type': photo.get_photo_type_display(),
            'photo_date': photo.photo_date.strftime('%d/%m/%Y'),
            'location_description': photo.location_description,
            'description': photo.description,
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


@login_required
@require_http_methods(["DELETE"])
def photo_delete(request, quotation_pk, photo_pk):
    """Vista AJAX para eliminar una foto"""
    try:
        quotation = get_object_or_404(Quotation, pk=quotation_pk)
        photo = get_object_or_404(QuotationPhotographicReport, pk=photo_pk, quotation=quotation)
        
        # Eliminar el archivo de imagen
        if photo.image:
            photo.image.delete()
        
        # Eliminar el objeto
        photo.delete()
        
        return JsonResponse({'success': True, 'message': 'Foto eliminada exitosamente'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

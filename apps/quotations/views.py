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
from .models import Quotation, QuotationItem, QuotationActivity
from apps.clients.models import Client
from apps.services.models import Service
import json

class QuotationListView(LoginRequiredMixin, ListView):
    model = Quotation
    template_name = 'quotations/list.html'
    context_object_name = 'quotations'
    paginate_by = 20
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('client')
        
        # Filtro por cliente
        client_id = self.request.GET.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
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
                Q(notes__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar listas para los filtros
        context['clients'] = Client.objects.all().order_by('name')
        context['status_choices'] = Quotation.STATUS_CHOICES
        
        # Mantener los valores de filtro actuales en el contexto
        context['current_client'] = self.request.GET.get('client')
        context['current_status'] = self.request.GET.get('status')
        context['current_search'] = self.request.GET.get('search', '')
        
        # Agregar objetos actuales para mostrar en los filtros activos
        if context['current_client']:
            try:
                context['current_client_obj'] = Client.objects.get(id=context['current_client'])
            except Client.DoesNotExist:
                context['current_client_obj'] = None
        
        if context['current_status']:
            context['current_status_display'] = dict(Quotation.STATUS_CHOICES).get(context['current_status'])
        
        return context

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar historial de actividades
        context['activities'] = self.object.activities.all().order_by('-created_at')[:20]
        return context

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
@require_POST
@csrf_exempt
def get_service_info(request):
    """Vista AJAX para obtener información de un servicio"""
    try:
        service_id = request.POST.get('service_id')
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

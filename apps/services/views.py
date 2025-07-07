from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Service, ServiceCategory, ServiceImage

# Vistas para Servicios
class ServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'services/list.html'
    context_object_name = 'services'
    paginate_by = 20
    ordering = ['category__name', 'name']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ServiceCategory.objects.all()
        return context

class ServiceDetailView(LoginRequiredMixin, DetailView):
    model = Service
    template_name = 'services/detail.html'
    context_object_name = 'service'

class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    template_name = 'services/form.html'
    fields = ['category', 'name', 'description', 'unit', 'unit_price', 'tax_rate', 'main_image', 'notes']
    success_url = reverse_lazy('services:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Servicio creado exitosamente.')
        return super().form_valid(form)

class ServiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Service
    template_name = 'services/form.html'
    fields = ['category', 'name', 'description', 'unit', 'unit_price', 'tax_rate', 'main_image', 'notes']
    success_url = reverse_lazy('services:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Servicio actualizado exitosamente.')
        return super().form_valid(form)

class ServiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Service
    template_name = 'services/delete.html'
    success_url = reverse_lazy('services:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Servicio eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

# Vistas para Categorías
class ServiceCategoryListView(LoginRequiredMixin, ListView):
    model = ServiceCategory
    template_name = 'services/category_list.html'
    context_object_name = 'categories'
    ordering = ['name']

class ServiceCategoryCreateView(LoginRequiredMixin, CreateView):
    model = ServiceCategory
    template_name = 'services/category_form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('services:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Categoría creada exitosamente.')
        return super().form_valid(form)

class ServiceCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ServiceCategory
    template_name = 'services/category_form.html'
    fields = ['name', 'description']
    success_url = reverse_lazy('services:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Categoría actualizada exitosamente.')
        return super().form_valid(form)

class ServiceCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ServiceCategory
    template_name = 'services/category_delete.html'
    success_url = reverse_lazy('services:category_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Categoría eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

# Vistas para Galería de Servicios
class ServiceGalleryView(LoginRequiredMixin, TemplateView):
    template_name = 'services/gallery.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = kwargs.get('pk')
        context['service'] = get_object_or_404(Service, pk=service_id)
        context['gallery_images'] = ServiceImage.objects.filter(service=context['service']).order_by('order', 'created_at')
        return context

class ServiceImageCreateView(LoginRequiredMixin, CreateView):
    model = ServiceImage
    template_name = 'services/add_image.html'
    fields = ['image', 'caption']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = self.kwargs.get('service_pk')
        context['service'] = get_object_or_404(Service, pk=service_id)
        return context
    
    def form_valid(self, form):
        service_id = self.kwargs.get('service_pk')
        service = get_object_or_404(Service, pk=service_id)
        form.instance.service = service
        messages.success(self.request, 'Imagen agregada exitosamente a la galería.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('services:gallery', kwargs={'pk': self.kwargs.get('service_pk')})

@login_required
@require_POST
def delete_service_image(request, pk, image_pk):
    """Vista AJAX para eliminar una imagen de la galería"""
    service = get_object_or_404(Service, pk=pk)
    image = get_object_or_404(ServiceImage, pk=image_pk, service=service)
    
    try:
        image.delete()
        messages.success(request, 'Imagen eliminada exitosamente.')
        return JsonResponse({
            'success': True,
            'message': 'Imagen eliminada exitosamente.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar la imagen: {str(e)}'
        })

@login_required
@require_POST
def move_service_image(request, pk, image_pk):
    """Vista AJAX para mover una imagen (subir/bajar)"""
    service = get_object_or_404(Service, pk=pk)
    image = get_object_or_404(ServiceImage, pk=image_pk, service=service)
    
    try:
        import json
        data = json.loads(request.body)
        direction = data.get('direction')
        
        if direction == 'up':
            image.up()
        elif direction == 'down':
            image.down()
        elif direction == 'top':
            image.top()
        elif direction == 'bottom':
            image.bottom()
        else:
            return JsonResponse({
                'success': False,
                'message': 'Dirección inválida'
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Imagen movida {direction} exitosamente.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al mover la imagen: {str(e)}'
        })

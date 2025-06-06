from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Service, ServiceCategory

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
    fields = ['category', 'name', 'description', 'unit', 'base_price', 'tax_rate', 'main_image']
    success_url = reverse_lazy('services:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Servicio creado exitosamente.')
        return super().form_valid(form)

class ServiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Service
    template_name = 'services/form.html'
    fields = ['category', 'name', 'description', 'unit', 'base_price', 'tax_rate', 'main_image']
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

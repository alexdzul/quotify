from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Client

# Create your views here.

class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'clients/list.html'
    context_object_name = 'clients'
    paginate_by = 20
    ordering = ['-created_at']

class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/detail.html'
    context_object_name = 'client'

class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    template_name = 'clients/form.html'
    fields = ['name', 'email', 'phone', 'address', 'city', 'state', 'postal_code', 'notes']
    success_url = reverse_lazy('clients:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Cliente creado exitosamente.')
        return super().form_valid(form)

class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    template_name = 'clients/form.html'
    fields = ['name', 'email', 'phone', 'address', 'city', 'state', 'postal_code', 'notes']
    success_url = reverse_lazy('clients:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return super().form_valid(form)

class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = 'clients/delete.html'
    success_url = reverse_lazy('clients:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Cliente eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

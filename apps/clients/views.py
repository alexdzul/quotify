from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Client, ClientNote
from .forms import ClientNoteForm

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        
        # Get client notes (exclude private notes unless user is the author)
        notes_queryset = client.client_notes.all()
        if not self.request.user.is_superuser:
            notes_queryset = notes_queryset.filter(
                Q(is_private=False) | Q(author=self.request.user)
            )
        
        context['recent_notes'] = notes_queryset[:5]
        context['notes_count'] = notes_queryset.count()
        context['unresolved_notes_count'] = notes_queryset.filter(is_resolved=False).count()
        
        return context

class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    template_name = 'clients/form.html'
    fields = ['name', 'email', 'phone', 'street', 'city', 'state', 'postal_code', 'notes', 'photo']
    success_url = reverse_lazy('clients:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Cliente creado exitosamente.')
        return super().form_valid(form)

class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    template_name = 'clients/form.html'
    fields = ['name', 'email', 'phone', 'street', 'city', 'state', 'postal_code', 'notes', 'photo']
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


# ==========================================
# CLIENT NOTES VIEWS
# ==========================================

class ClientNoteListView(LoginRequiredMixin, ListView):
    model = ClientNote
    template_name = 'clients/notes/list.html'
    context_object_name = 'notes'
    paginate_by = 20
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.kwargs.get('client_pk')
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter private notes unless user is author or superuser
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(is_private=False) | Q(author=self.request.user)
            )
        
        # Apply filters from GET parameters
        note_type = self.request.GET.get('type')
        if note_type:
            queryset = queryset.filter(note_type=note_type)
        
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        status = self.request.GET.get('status')
        if status == 'resolved':
            queryset = queryset.filter(is_resolved=True)
        elif status == 'unresolved':
            queryset = queryset.filter(is_resolved=False)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(content__icontains=search) |
                Q(client__name__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client_id = self.kwargs.get('client_pk')
        
        if client_id:
            context['client'] = get_object_or_404(Client, pk=client_id)
        
        # Add filter options for template
        context['type_choices'] = ClientNote.TYPE_CHOICES
        context['priority_choices'] = ClientNote.PRIORITY_CHOICES
        context['current_filters'] = {
            'type': self.request.GET.get('type', ''),
            'priority': self.request.GET.get('priority', ''),
            'status': self.request.GET.get('status', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        return context


class ClientNoteDetailView(LoginRequiredMixin, DetailView):
    model = ClientNote
    template_name = 'clients/notes/detail.html'
    context_object_name = 'note'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter private notes unless user is author or superuser
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(is_private=False) | Q(author=self.request.user)
            )
        return queryset


class ClientNoteCreateView(LoginRequiredMixin, CreateView):
    model = ClientNote
    form_class = ClientNoteForm
    template_name = 'clients/notes/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client_id = self.kwargs.get('client_pk')
        if client_id:
            context['client'] = get_object_or_404(Client, pk=client_id)
        return context
    
    def form_valid(self, form):
        # Set the client and author
        client_id = self.kwargs.get('client_pk')
        if client_id:
            form.instance.client = get_object_or_404(Client, pk=client_id)
        form.instance.author = self.request.user
        
        messages.success(self.request, 'Nota creada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        client_id = self.kwargs.get('client_pk')
        if client_id:
            return reverse('clients:note_list', kwargs={'client_pk': client_id})
        return reverse('clients:note_list_all')


class ClientNoteUpdateView(LoginRequiredMixin, UpdateView):
    model = ClientNote
    form_class = ClientNoteForm
    template_name = 'clients/notes/form.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only allow editing own notes unless superuser
        if not self.request.user.is_superuser:
            queryset = queryset.filter(author=self.request.user)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_object().client
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Nota actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('clients:note_detail', kwargs={'pk': self.object.pk})


class ClientNoteDeleteView(LoginRequiredMixin, DeleteView):
    model = ClientNote
    template_name = 'clients/notes/delete.html'
    context_object_name = 'note'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only allow deleting own notes unless superuser
        if not self.request.user.is_superuser:
            queryset = queryset.filter(author=self.request.user)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.get_object().client
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Nota eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        client = self.get_object().client
        return reverse('clients:note_list', kwargs={'client_pk': client.pk})


# ==========================================
# AJAX VIEWS FOR CLIENT NOTES
# ==========================================

@login_required
@require_POST
def toggle_note_resolved(request, pk):
    """AJAX view to toggle note resolved status"""
    try:
        note = get_object_or_404(ClientNote, pk=pk)
        
        # Check permissions
        if not request.user.is_superuser and note.author != request.user:
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Toggle resolved status
        note.is_resolved = not note.is_resolved
        if note.is_resolved:
            note.resolved_at = timezone.now()
        else:
            note.resolved_at = None
        note.save()
        
        return JsonResponse({
            'success': True,
            'is_resolved': note.is_resolved,
            'resolved_at': note.resolved_at.strftime('%d/%m/%Y %H:%M') if note.resolved_at else None
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

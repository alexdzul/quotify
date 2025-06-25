from django.contrib import admin
from .models import Client, ClientNote


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'email', 
        'phone', 
        'city', 
        'state', 
        'get_quotations_count',
        'is_active',
        'created_at'
    ]
    list_filter = ['is_active', 'state', 'country', 'created_at']
    search_fields = ['name', 'email', 'phone', 'city']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'email', 'phone', 'is_active')
        }),
        ('Dirección', {
            'fields': ('street', 'city', 'state', 'postal_code', 'country')
        }),
        ('Información Adicional', {
            'fields': ('notes',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Pagination
    list_per_page = 25
    
    # Export actions
    actions = ['activate_clients', 'deactivate_clients']
    
    def activate_clients(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} clientes activados.')
    activate_clients.short_description = "Activar clientes seleccionados"
    
    def deactivate_clients(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} clientes desactivados.')
    deactivate_clients.short_description = "Desactivar clientes seleccionados"


@admin.register(ClientNote)
class ClientNoteAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'client',
        'author',
        'note_type',
        'priority',
        'is_resolved',
        'is_private',
        'created_at'
    ]
    list_filter = [
        'note_type',
        'priority',
        'is_resolved',
        'is_private',
        'created_at',
        'follow_up_date'
    ]
    search_fields = ['title', 'content', 'client__name', 'author__username']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('client', 'author', 'title', 'content')
        }),
        ('Clasificación', {
            'fields': ('note_type', 'priority')
        }),
        ('Estado y Visibilidad', {
            'fields': ('is_resolved', 'is_private', 'follow_up_date')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Pagination
    list_per_page = 25
    
    # Filters
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Show only own notes for non-superusers
            qs = qs.filter(author=request.user)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new note
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    # Actions
    actions = ['mark_resolved', 'mark_unresolved', 'mark_private', 'mark_public']
    
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{updated} notas marcadas como resueltas.')
    mark_resolved.short_description = "Marcar como resueltas"
    
    def mark_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False, resolved_at=None)
        self.message_user(request, f'{updated} notas marcadas como no resueltas.')
    mark_unresolved.short_description = "Marcar como no resueltas"
    
    def mark_private(self, request, queryset):
        updated = queryset.update(is_private=True)
        self.message_user(request, f'{updated} notas marcadas como privadas.')
    mark_private.short_description = "Marcar como privadas"
    
    def mark_public(self, request, queryset):
        updated = queryset.update(is_private=False)
        self.message_user(request, f'{updated} notas marcadas como públicas.')
    mark_public.short_description = "Marcar como públicas"

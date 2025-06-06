from django.contrib import admin
from .models import Client


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

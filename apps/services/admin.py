from django.contrib import admin
from django.utils.html import format_html
from .models import ServiceCategory, Service, ServiceImage


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Fechas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 1
    fields = ['image', 'caption', 'order']
    readonly_fields = []
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return self.readonly_fields + ['image_preview']
        return self.readonly_fields
    
    def image_preview(self, obj):
        if obj and obj.pk and obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 150px;" />', obj.image.url)
        return "No hay imagen"
    image_preview.short_description = "Vista Previa"


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'category', 
        'unit_price', 
        'unit', 
        'tax_rate',
        'get_image_preview',
        'is_active',
        'created_at'
    ]
    list_filter = ['category', 'unit', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return self.readonly_fields + ['get_image_preview']
        return self.readonly_fields
    inlines = [ServiceImageInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'category', 'is_active')
        }),
        ('Imagen Principal', {
            'fields': ('main_image',)
        }),
        ('Precios e Impuestos', {
            'fields': ('unit_price', 'unit', 'tax_rate')
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
    
    # Filters
    list_editable = ['unit_price', 'tax_rate', 'is_active']
    
    # Actions
    actions = ['activate_services', 'deactivate_services', 'update_tax_rate']
    
    def activate_services(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} servicios activados.')
    activate_services.short_description = "Activar servicios seleccionados"
    
    def deactivate_services(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} servicios desactivados.')
    deactivate_services.short_description = "Desactivar servicios seleccionados"
    
    def update_tax_rate(self, request, queryset):
        # This would need a form to get the new tax rate
        # For now, just set to default 16%
        updated = queryset.update(tax_rate=16.00)
        self.message_user(request, f'Tasa de impuesto actualizada para {updated} servicios.')
    update_tax_rate.short_description = "Actualizar tasa de impuesto a 16 por ciento"
    
    def get_image_preview(self, obj):
        if obj and obj.pk and obj.main_image:
            try:
                return format_html('<img src="{}" style="max-height: 50px; max-width: 75px;" />', obj.main_image.url)
            except:
                return "Error al cargar imagen"
        return "Sin imagen"
    get_image_preview.short_description = "Imagen"


@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = ['service', 'image_preview', 'caption', 'order', 'created_at']
    list_filter = ['service__category', 'created_at']
    search_fields = ['service__name', 'caption']
    readonly_fields = ['image_preview', 'created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('service', 'image', 'image_preview')
        }),
        ('Detalles', {
            'fields': ('caption', 'order')
        }),
        ('Fechas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj and obj.pk and obj.image:
            try:
                return format_html('<img src="{}" style="max-height: 150px; max-width: 200px;" />', obj.image.url)
            except:
                return "Error al cargar imagen"
        return "No hay imagen"
    image_preview.short_description = "Vista Previa"

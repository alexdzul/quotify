from django.contrib import admin
from django.utils.html import format_html
from .models import Quotation, QuotationItem, QuotationItemImage, QuotationPhotographicReport, QuotationActivity


class QuotationItemImageInline(admin.TabularInline):
    model = QuotationItemImage
    extra = 0
    fields = ['image', 'caption', 'order']
    readonly_fields = []
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return self.readonly_fields + ['image_preview']
        return self.readonly_fields
    
    def image_preview(self, obj):
        if obj and obj.pk and obj.image:
            try:
                return format_html('<img src="{}" style="max-height: 80px; max-width: 120px;" />', obj.image.url)
            except:
                return "Error al cargar imagen"
        return "No hay imagen"
    image_preview.short_description = "Vista Previa"


class QuotationPhotographicReportInline(admin.TabularInline):
    model = QuotationPhotographicReport
    extra = 0
    fields = ['image', 'photo_type', 'title', 'location_description', 'order']
    readonly_fields = []
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return self.readonly_fields + ['image_preview']
        return self.readonly_fields
    
    def image_preview(self, obj):
        if obj and obj.pk and obj.image:
            try:
                return format_html('<img src="{}" style="max-height: 80px; max-width: 120px;" />', obj.image.url)
            except:
                return "Error al cargar imagen"
        return "No hay imagen"
    image_preview.short_description = "Vista Previa"


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 1
    fields = [
        'service', 
        'quantity', 
        'unit_price', 
        'tax_rate',
        'custom_image',
        'description',
        'order'
    ]
    readonly_fields = []
    
    def get_readonly_fields(self, request, obj=None):
        # Make unit_price and tax_rate readonly if service is selected
        # This could be enhanced with JavaScript
        base_readonly = self.readonly_fields[:]
        if obj and obj.pk:
            base_readonly.append('get_image_preview')
        return base_readonly
    
    def get_image_preview(self, obj):
        if obj and obj.pk and obj.display_image:
            try:
                return format_html('<img src="{}" style="max-height: 50px; max-width: 75px;" />', obj.display_image.url)
            except:
                return "Error al cargar imagen"
        return "Sin imagen"
    get_image_preview.short_description = "Imagen"


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = [
        'quotation_number',
        'client',
        'salesperson',
        'quotation_date',
        'expiration_date',
        'status',
        'get_total_amount',
        'get_photographic_report_count',
        'get_status_badge'
    ]
    list_filter = [
        'status', 
        'quotation_date', 
        'expiration_date', 
        'salesperson',
        'created_at'
    ]
    search_fields = [
        'quotation_number', 
        'client__name', 
        'client__email',
        'salesperson__first_name',
        'salesperson__last_name'
    ]
    readonly_fields = [
        'quotation_number', 
        'uuid',
        'created_at', 
        'updated_at',
        'get_subtotal',
        'get_tax_amount', 
        'get_total_amount',
        'get_photographic_report_count'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'quotation_number',
                'client', 
                'salesperson',
                'status'
            )
        }),
        ('Fechas', {
            'fields': (
                'quotation_date', 
                'expiration_date'
            )
        }),
        ('Información de la Empresa', {
            'fields': (
                'company_name',
                'company_address'
            ),
            'classes': ('collapse',)
        }),
        ('Términos y Condiciones', {
            'fields': (
                'payment_terms',
                'terms_and_conditions',
                'notes'
            )
        }),
        ('Totales', {
            'fields': (
                'get_subtotal',
                'get_tax_amount',
                'get_total_amount'
            ),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': (
                'uuid',
                'created_at', 
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [QuotationItemInline, QuotationPhotographicReportInline]
    
    # Pagination
    list_per_page = 25
    
    # Actions
    actions = [
        'mark_as_sent', 
        'mark_as_accepted', 
        'mark_as_rejected',
        'mark_as_draft'
    ]
    
    def get_total_amount(self, obj):
        return f"${obj.total_amount:,.2f}"
    get_total_amount.short_description = "Total"
    
    def get_subtotal(self, obj):
        return f"${obj.subtotal:,.2f}"
    get_subtotal.short_description = "Subtotal"
    
    def get_tax_amount(self, obj):
        return f"${obj.tax_amount:,.2f}"
    get_tax_amount.short_description = "Impuestos"
    
    def get_status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'sent': '#007bff', 
            'accepted': '#28a745',
            'rejected': '#dc3545',
            'expired': '#fd7e14'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = "Estado"
    
    # Actions
    def mark_as_sent(self, request, queryset):
        updated = queryset.update(status='sent')
        self.message_user(request, f'{updated} cotizaciones marcadas como enviadas.')
    mark_as_sent.short_description = "Marcar como enviadas"
    
    def mark_as_accepted(self, request, queryset):
        updated = queryset.update(status='accepted')
        self.message_user(request, f'{updated} cotizaciones marcadas como aceptadas.')
    mark_as_accepted.short_description = "Marcar como aceptadas"
    
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} cotizaciones marcadas como rechazadas.')
    mark_as_rejected.short_description = "Marcar como rechazadas"
    
    def mark_as_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} cotizaciones marcadas como borrador.')
    mark_as_draft.short_description = "Marcar como borrador"


@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    list_display = [
        'quotation',
        'service',
        'quantity',
        'unit_price',
        'get_subtotal',
        'tax_rate',
        'get_image_preview',
        'get_total_amount'
    ]
    list_filter = [
        'quotation__status',
        'service__category',
        'tax_rate'
    ]
    search_fields = [
        'quotation__quotation_number',
        'quotation__client__name',
        'service__name'
    ]
    readonly_fields = [
        'get_subtotal',
        'get_tax_amount',
        'get_total_amount',
        'get_image_preview',
        'created_at',
        'updated_at'
    ]
    inlines = [QuotationItemImageInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('quotation', 'service', 'quantity', 'unit_price', 'tax_rate')
        }),
        ('Personalización', {
            'fields': ('description', 'custom_image', 'get_image_preview', 'order')
        }),
        ('Totales', {
            'fields': ('get_subtotal', 'get_tax_amount', 'get_total_amount'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_subtotal(self, obj):
        return f"${obj.subtotal:,.2f}"
    get_subtotal.short_description = "Subtotal"
    
    def get_tax_amount(self, obj):
        return f"${obj.tax_amount:,.2f}"
    get_tax_amount.short_description = "Impuestos"
    
    def get_total_amount(self, obj):
        return f"${obj.total_amount:,.2f}"
    get_total_amount.short_description = "Total"
    
    def get_image_preview(self, obj):
        if obj and obj.pk and obj.display_image:
            try:
                return format_html('<img src="{}" style="max-height: 50px; max-width: 75px;" />', obj.display_image.url)
            except:
                return "Error al cargar imagen"
        return "Sin imagen"
    get_image_preview.short_description = "Imagen"


@admin.register(QuotationItemImage)
class QuotationItemImageAdmin(admin.ModelAdmin):
    list_display = ['quotation_item', 'image_preview', 'caption', 'order', 'created_at']
    list_filter = ['quotation_item__quotation__status', 'created_at']
    search_fields = ['quotation_item__quotation__quotation_number', 'caption']
    readonly_fields = ['image_preview', 'created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('quotation_item', 'image', 'image_preview')
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


@admin.register(QuotationPhotographicReport)
class QuotationPhotographicReportAdmin(admin.ModelAdmin):
    list_display = [
        'quotation', 
        'photo_type', 
        'display_title', 
        'location_description',
        'photo_date',
        'order',
        'image_preview'
    ]
    list_filter = [
        'photo_type', 
        'quotation__status',
        'photo_date',
        'created_at'
    ]
    search_fields = [
        'quotation__quotation_number',
        'quotation__client__name',
        'title',
        'description',
        'location_description'
    ]
    readonly_fields = [
        'image_preview',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Informacion Basica', {
            'fields': ('quotation', 'image', 'image_preview')
        }),
        ('Clasificacion', {
            'fields': ('photo_type', 'title', 'location_description')
        }),
        ('Descripcion', {
            'fields': ('description',)
        }),
        ('Fecha y Orden', {
            'fields': ('photo_date', 'order')
        }),
        ('Fechas del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Pagination
    list_per_page = 25
    
    # Filter by quotation status
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('quotation', 'quotation__client')
    
    def image_preview(self, obj):
        if obj and obj.pk and obj.image:
            try:
                return format_html('<img src="{}" style="max-height: 100px; max-width: 150px;" />', obj.image.url)
            except:
                return "Error al cargar imagen"
        return "No hay imagen"
    image_preview.short_description = "Vista Previa"
    
    def display_title(self, obj):
        return obj.display_title
    display_title.short_description = "Titulo"


@admin.register(QuotationActivity)
class QuotationActivityAdmin(admin.ModelAdmin):
    list_display = [
        'quotation',
        'activity_type',
        'title',
        'user',
        'get_priority_badge',
        'get_status_badge',
        'created_at'
    ]
    list_filter = [
        'activity_type',
        'priority',
        'is_automatic',
        'requires_follow_up',
        'quotation__status',
        'created_at'
    ]
    search_fields = [
        'quotation__quotation_number',
        'quotation__client__name',
        'title',
        'description',
        'contact_person',
        'contact_email'
    ]
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'quotation',
                'activity_type',
                'title',
                'description'
            )
        }),
        ('Estado y Cambios', {
            'fields': (
                'old_status',
                'new_status'
            ),
            'classes': ('collapse',)
        }),
        ('Programación', {
            'fields': (
                'scheduled_date',
                'completed_date',
                'priority'
            )
        }),
        ('Seguimiento', {
            'fields': (
                'requires_follow_up',
                'follow_up_date'
            )
        }),
        ('Información de Contacto', {
            'fields': (
                'contact_person',
                'contact_email',
                'contact_phone'
            ),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': (
                'user',
                'is_automatic',
                'additional_data'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas del Sistema', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    # Pagination
    list_per_page = 25
    
    # Actions
    actions = ['mark_completed', 'add_follow_up', 'set_high_priority']
    
    def get_priority_badge(self, obj):
        colors = {
            'low': '#28a745',
            'normal': '#6c757d',
            'high': '#fd7e14',
            'urgent': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    get_priority_badge.short_description = "Prioridad"
    
    def get_status_badge(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ Completada</span>')
        elif obj.is_overdue:
            return format_html('<span style="color: #dc3545; font-weight: bold;">⚠ Vencida</span>')
        elif obj.scheduled_date:
            return format_html('<span style="color: #fd7e14; font-weight: bold;">⏰ Programada</span>')
        elif obj.needs_follow_up:
            return format_html('<span style="color: #007bff; font-weight: bold;">📝 Seguimiento</span>')
        else:
            return format_html('<span style="color: #6c757d;">📋 Registrada</span>')
    get_status_badge.short_description = "Estado"
    
    # Custom actions
    def mark_completed(self, request, queryset):
        updated = 0
        for activity in queryset:
            if not activity.is_completed:
                activity.mark_completed()
                updated += 1
        self.message_user(request, f'{updated} actividades marcadas como completadas.')
    mark_completed.short_description = "Marcar como completadas"
    
    def add_follow_up(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        follow_up_date = timezone.now() + timedelta(days=7)
        updated = queryset.update(
            requires_follow_up=True,
            follow_up_date=follow_up_date
        )
        self.message_user(request, f'{updated} actividades configuradas para seguimiento en 7 días.')
    add_follow_up.short_description = "Agregar seguimiento en 7 días"
    
    def set_high_priority(self, request, queryset):
        updated = queryset.update(priority='high')
        self.message_user(request, f'{updated} actividades marcadas como alta prioridad.')
    set_high_priority.short_description = "Marcar como alta prioridad"



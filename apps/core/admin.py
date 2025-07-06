from django.contrib import admin
from django.utils.html import format_html
from .models import CompanyProfile, SystemSettings, SalesPerson


@admin.register(SalesPerson)
class SalesPersonAdmin(admin.ModelAdmin):
    list_display = [
        'full_name',
        'email',
        'phone',
        'employee_id',
        'department',
        'commission_rate',
        'get_quotations_count',
        'get_performance_badge',
        'is_active',
        'hire_date'
    ]
    list_filter = [
        'is_active',
        'department',
        'hire_date',
        'created_at'
    ]
    search_fields = [
        'first_name',
        'last_name',
        'email',
        'employee_id'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'get_quotations_count',
        'get_total_sales_display',
        'get_commission_earned_display'
    ]
    
    fieldsets = (
        ('Información Personal', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'phone',
                'profile_photo',
                'is_active'
            )
        }),
        ('Información Laboral', {
            'fields': (
                'employee_id',
                'department',
                'hire_date',
                'commission_rate'
            )
        }),
        ('Información Adicional', {
            'fields': ('notes',)
        }),
        ('Rendimiento', {
            'fields': (
                'get_quotations_count',
                'get_total_sales_display',
                'get_commission_earned_display'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Pagination
    list_per_page = 25
    
    # Actions
    actions = ['activate_salespersons', 'deactivate_salespersons']
    
    def get_performance_badge(self, obj):
        quotations_count = obj.get_quotations_count()
        if quotations_count >= 10:
            color = '#28a745'  # green
            status = 'Alto'
        elif quotations_count >= 5:
            color = '#ffc107'  # yellow
            status = 'Medio'
        else:
            color = '#6c757d'  # gray
            status = 'Bajo'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status
        )
    get_performance_badge.short_description = "Rendimiento"
    
    def get_total_sales_display(self, obj):
        total = obj.get_total_sales_amount()
        return f"${total:,.2f}"
    get_total_sales_display.short_description = "Total Ventas Aceptadas"
    
    def get_commission_earned_display(self, obj):
        commission = obj.get_commission_earned()
        return f"${commission:,.2f}"
    get_commission_earned_display.short_description = "Comision Ganada"
    
    def activate_salespersons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} vendedores activados.')
    activate_salespersons.short_description = "Activar vendedores seleccionados"
    
    def deactivate_salespersons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} vendedores desactivados.')
    deactivate_salespersons.short_description = "Desactivar vendedores seleccionados"


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'email', 
        'phone', 
        'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slogan', 'email', 'phone', 'website')
        }),
        ('Dirección', {
            'fields': ('address',)
        }),
        ('Redes Sociales', {
            'fields': ('facebook_url', 'instagram_url', 'tiktok_url')
        }),
        ('Imágenes', {
            'fields': ('logo', 'cover_image')
        }),
        ('Configuraciones por Defecto', {
            'fields': ('default_tax_rate', 'default_payment_terms')
        }),
        ('Términos y Condiciones', {
            'fields': ('terms_and_conditions',),
            'description': 'Términos y condiciones completos que aparecerán en las cotizaciones'
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Removed restriction - multiple company profiles are now allowed


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'system_name',
        'primary_color',
        'quotation_validity_days',
        'quotation_number_prefix',
        'currency_symbol',
        'enable_notifications',
        'updated_at'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Apariencia', {
            'fields': (
                'system_name',
                'primary_color'
            )
        }),
        ('Configuración de Cotizaciones', {
            'fields': (
                'quotation_validity_days',
                'quotation_number_prefix'
            )
        }),
        ('Configuración de Moneda', {
            'fields': (
                'currency_symbol',
                'currency_code'
            )
        }),
        ('Configuración de Email', {
            'fields': (
                'default_email_from',
            )
        }),
        ('Otras Configuraciones', {
            'fields': (
                'enable_notifications',
            )
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings object
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False



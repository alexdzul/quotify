from django.db import models
from django.core.validators import MinValueValidator, EmailValidator, RegexValidator
from decimal import Decimal


class SalesPerson(models.Model):
    """Model to represent salespersons"""
    
    # Basic information
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellidos")
    email = models.EmailField(
        validators=[EmailValidator()], 
        unique=True,
        verbose_name="Email"
    )
    phone = models.CharField(
        max_length=20, 
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')],
        blank=True,
        null=True,
        verbose_name="Teléfono",
        help_text="Formato: +999999999. Hasta 15 dígitos permitidos."
    )
    
    # Employment information
    employee_id = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True,
        verbose_name="ID Empleado",
        help_text="Código único del empleado"
    )
    department = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Departamento"
    )
    hire_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Fecha de Contratación"
    )
    
    # Performance tracking
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Tasa de Comisión (%)",
        help_text="Porcentaje de comisión sobre ventas"
    )
    
    # Profile photo
    profile_photo = models.ImageField(
        upload_to='salespersons/',
        blank=True,
        null=True,
        verbose_name="Foto de Perfil",
        help_text="Foto del vendedor para mostrar en cotizaciones"
    )
    
    # Additional information
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    # Status and timestamps
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Vendedor"
        verbose_name_plural = "Vendedores"
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """Return the complete name"""
        return f"{self.first_name} {self.last_name}"

    def get_quotations_count(self):
        """Return the number of quotations for this salesperson"""
        return self.quotations.count()

    get_quotations_count.short_description = "Cotizaciones"

    def get_total_sales_amount(self):
        """Calculate total sales amount from accepted quotations"""
        accepted_quotations = self.quotations.filter(status='accepted')
        return sum(quotation.total_amount for quotation in accepted_quotations)

    def get_commission_earned(self):
        """Calculate commission earned from accepted quotations"""
        total_sales = self.get_total_sales_amount()
        return total_sales * (self.commission_rate / Decimal('100'))


class CompanyProfile(models.Model):
    """Company profile information for quotations"""
    
    name = models.CharField(max_length=200, verbose_name="Nombre de la Empresa")
    address = models.TextField(verbose_name="Dirección")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Sitio Web")
    
    # Social media
    facebook_url = models.URLField(blank=True, verbose_name="Facebook")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram")
    tiktok_url = models.URLField(blank=True, verbose_name="TikTok")
    
    # Logo
    logo = models.ImageField(
        upload_to='company/', 
        blank=True, 
        null=True,
        verbose_name="Logo"
    )
    
    # Cover image for quotations
    cover_image = models.ImageField(
        upload_to='company/covers/',
        blank=True,
        null=True,
        verbose_name="Imagen de Portada",
        help_text="Imagen principal que aparecerá en la portada de las cotizaciones"
    )
    
    # Company slogan for quotations
    slogan = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Slogan de la Empresa",
        help_text="Slogan que aparecerá en la portada de las cotizaciones (ej: 'NUESTRO COMPROMISO: SU JARDÍN')"
    )
    
    # Company brand color for quotations
    COLOR_CHOICES = [
        ('#2c5f2d', 'Verde (Predeterminado)'),
        ('#1e3a8a', 'Azul'),
        ('#7c3aed', 'Morado'),
        ('#dc2626', 'Rojo'),
        ('#ea580c', 'Naranja'),
        ('#0891b2', 'Cian'),
        ('#059669', 'Esmeralda'),
        ('#7c2d12', 'Café'),
        ('#374151', 'Gris'),
        ('#be123c', 'Rosa'),
        ('#4338ca', 'Índigo'),
        ('#a21caf', 'Fucsia'),
    ]
    
    brand_color = models.CharField(
        max_length=7,
        choices=COLOR_CHOICES,
        default='#2c5f2d',
        verbose_name="Color de la Empresa",
        help_text="Color principal que se utilizará en las cotizaciones de esta empresa"
    )
    
    # Default values
    default_tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=16.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Tasa de Impuesto por Defecto (%)"
    )
    
    default_payment_terms = models.TextField(
        default="Anticipo del 60% para la programación de los trabajos.\nSaldo del 40% al término de los mismos.",
        verbose_name="Términos de Pago por Defecto"
    )
    
    # Complete Terms and Conditions
    terms_and_conditions = models.TextField(
        blank=True,
        verbose_name="Términos y Condiciones Completos",
        help_text="Términos y condiciones detallados que aparecerán en las cotizaciones",
        default="""1. Orders and Payments
ESTOS PRECIOS NO INCLUYEN IVA.
En caso de requerir facturase incrementa el 16% correspondiente.
Cada cotización tendrá su especificaciones de métodos y porcentajes de pago.

2. Product Descriptions
LAS FOTOS EN ESTE PRESUPUESTO SON ILUSTRATIVAS SEMEJANDO EL PRODUCTO COTIZADO.

3. Shipping and Delivery
TIEMPO DE ENTREGA 7 DÍAS HÁBILES.
EN CASO DE DESASTRE NATURAL SE VOLVERÁ A CONFIRMAR EL TIEMPO DE ENTREGA

4. WARRANTY.
SE OTORGA GARANTÍA EN PASTO POR 30 DÍAS.
SE OTORGA GARANTÍA EN PLANTAS POR 60 DÍAS.
SE OTORGA GARANTÍA EN ÁRBOLES POR 6 MESES.
APLICA GARANTÍA MENCIONADA SI Y SOLO SI SE CONTRATAN LOS SERVICIOS DE SISTEMA DE RIEGO AUTOMÁTICO.
NO APLICA EN CASO DE FALLO DE LUZ ELÉCTRICA PROPORCIONADA POR CLIENTE. NO APLICA EN CASO DE DESASTRE NATURAL."""
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de la Empresa"
        verbose_name_plural = "Perfiles de la Empresa"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_quotations_count(self):
        """Return the number of quotations for this company profile"""
        return self.quotations.count()

    def get_accepted_quotations_count(self):
        """Return the number of accepted quotations"""
        return self.quotations.filter(status='accepted').count()

    def get_conversion_rate(self):
        """Calculate the conversion rate of quotations"""
        total = self.get_quotations_count()
        if total == 0:
            return 0
        accepted = self.get_accepted_quotations_count()
        return (accepted / total) * 100

    def get_total_quoted_value(self):
        """Calculate total value of all quotations"""
        return sum(q.total_amount for q in self.quotations.all())

    def get_accepted_value(self):
        """Calculate total value of accepted quotations"""
        return sum(q.total_amount for q in self.quotations.filter(status='accepted'))

    def get_pending_value(self):
        """Calculate total value of pending quotations (draft + sent)"""
        return sum(q.total_amount for q in self.quotations.filter(status__in=['draft', 'sent']))

    def get_recent_quotation_date(self):
        """Get the date of the most recent quotation"""
        recent_quotation = self.quotations.order_by('-created_at').first()
        return recent_quotation.created_at if recent_quotation else None

    def has_activity(self):
        """Check if the company profile has any quotations"""
        return self.get_quotations_count() > 0

    @property
    def activity_level(self):
        """Return activity level based on number of quotations"""
        count = self.get_quotations_count()
        if count == 0:
            return 'inactive'
        elif count <= 5:
            return 'low'
        elif count <= 15:
            return 'medium'
        else:
            return 'high'

    get_quotations_count.short_description = "Cotizaciones"
    get_accepted_quotations_count.short_description = "Aceptadas"


class SystemSettings(models.Model):
    """System-wide settings and configuration"""
    
    COLOR_CHOICES = [
        ('primary', 'Azul (Predeterminado)'),
        ('success', 'Verde'),
        ('info', 'Cian'),
        ('warning', 'Amarillo'),
        ('danger', 'Rojo'),
        ('dark', 'Negro'),
        ('purple', 'Morado'),
        ('pink', 'Rosa'),
        ('orange', 'Naranja'),
        ('teal', 'Verde Azulado'),
        ('indigo', 'Índigo'),
    ]
    
    # Appearance settings
    primary_color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        default='primary',
        verbose_name="Color Principal de la Plataforma"
    )
    
    # System settings
    system_name = models.CharField(
        max_length=100,
        default="Quotify",
        verbose_name="Nombre del Sistema"
    )
    
    # Quotation settings
    quotation_validity_days = models.PositiveIntegerField(
        default=7,
        verbose_name="Días de Validez de Cotización"
    )
    
    quotation_number_prefix = models.CharField(
        max_length=10,
        default="S",
        verbose_name="Prefijo del Número de Cotización"
    )
    
    # Currency settings
    currency_symbol = models.CharField(
        max_length=5,
        default="$",
        verbose_name="Símbolo de Moneda"
    )
    currency_code = models.CharField(
        max_length=3,
        default="MXN",
        verbose_name="Código de Moneda"
    )
    
    # Email settings
    default_email_from = models.EmailField(
        blank=True,
        verbose_name="Email de Envío por Defecto"
    )
    
    # Other settings
    enable_notifications = models.BooleanField(
        default=True,
        verbose_name="Habilitar Notificaciones"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"

    def __str__(self):
        return f"Configuración del Sistema - {self.system_name}"

    def save(self, *args, **kwargs):
        # Ensure only one settings object exists
        if not self.pk and SystemSettings.objects.exists():
            raise ValueError("Solo puede existir una configuración del sistema")
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get system settings, create if doesn't exist"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'primary_color': 'primary',
                'system_name': 'Quotify',
                'quotation_validity_days': 7,
                'quotation_number_prefix': 'S',
                'currency_symbol': '$',
                'currency_code': 'MXN',
                'enable_notifications': True,
            }
        )
        return settings



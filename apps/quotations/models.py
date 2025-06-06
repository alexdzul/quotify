from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

from apps.clients.models import Client
from apps.services.models import Service
from apps.core.models import SalesPerson


class Quotation(models.Model):
    """Main quotation model"""
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('sent', 'Enviada'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('expired', 'Expirada'),
    ]
    
    # Identification
    quotation_number = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="Número de Cotización",
        help_text="Ejemplo: S00101"
    )
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Client information
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='quotations',
        verbose_name="Cliente"
    )
    
    # Salesperson information
    salesperson = models.ForeignKey(
        SalesPerson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations',
        verbose_name="Vendedor"
    )
    
    # Dates
    quotation_date = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de Cotización"
    )
    expiration_date = models.DateField(
        verbose_name="Fecha de Expiración"
    )
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        verbose_name="Estado"
    )
    
    # Payment terms
    payment_terms = models.TextField(
        verbose_name="Términos de Pago",
        default="Anticipo del 60% para la programación de los trabajos.\nSaldo del 40% al término de los mismos."
    )
    
    # Terms and conditions
    terms_and_conditions = models.TextField(
        blank=True,
        verbose_name="Términos y Condiciones",
        help_text="Se llenarán automáticamente desde el perfil de la empresa"
    )
    
    # Additional information
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    # Company information (can be made configurable later)
    company_name = models.CharField(
        max_length=200, 
        default="Total Garden & Pool",
        verbose_name="Nombre de la Empresa"
    )
    company_address = models.TextField(
        default="Calle 9 No. 167 x 16 y 18\nColonia. Mulsay CP. 97249\nMérida Yucatán\nMéxico.",
        verbose_name="Dirección de la Empresa"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Cotizacion"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-quotation_date', '-created_at']

    def __str__(self):
        return f"{self.quotation_number} - {self.client.name}"

    def save(self, *args, **kwargs):
        # Import here to avoid circular imports
        from apps.core.models import CompanyProfile
        
        if not self.quotation_number:
            # Generate quotation number automatically
            last_quotation = Quotation.objects.filter(
                quotation_number__startswith='S'
            ).order_by('-quotation_number').first()
            
            if last_quotation:
                try:
                    last_number = int(last_quotation.quotation_number[1:])
                    new_number = last_number + 1
                except ValueError:
                    new_number = 1
            else:
                new_number = 1
            
            self.quotation_number = f'S{new_number:05d}'
        
        # Auto-populate company information from active profile
        if not self.pk:  # Only for new quotations
            active_profile = CompanyProfile.get_active_profile()
            if active_profile:
                if not self.company_name:
                    self.company_name = active_profile.name
                if not self.company_address:
                    self.company_address = active_profile.address
                if not self.payment_terms or self.payment_terms == "Anticipo del 60% para la programación de los trabajos.\nSaldo del 40% al término de los mismos.":
                    self.payment_terms = active_profile.default_payment_terms
                if not self.terms_and_conditions:
                    self.terms_and_conditions = active_profile.terms_and_conditions
        
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Calculate subtotal (before taxes)"""
        return sum(item.subtotal for item in self.items.all())

    @property
    def tax_amount(self):
        """Calculate total tax amount"""
        return sum(item.tax_amount for item in self.items.all())

    @property
    def total_amount(self):
        """Calculate total amount (including taxes)"""
        return self.subtotal + self.tax_amount

    @property
    def is_expired(self):
        """Check if quotation has expired"""
        return timezone.now().date() > self.expiration_date

    def get_advance_payment(self, percentage=60):
        """Calculate advance payment based on percentage"""
        return self.total_amount * Decimal(str(percentage)) / Decimal('100')

    def get_balance_payment(self, percentage=40):
        """Calculate balance payment based on percentage"""
        return self.total_amount * Decimal(str(percentage)) / Decimal('100')

    def get_photographic_report_count(self):
        """Return the number of photos in photographic report"""
        return self.photographic_report.count()

    get_photographic_report_count.short_description = "Fotos de Evidencia"


class QuotationPhotographicReport(models.Model):
    """Photographic evidence/report for quotations (before, during, after work)"""
    
    PHOTO_TYPE_CHOICES = [
        ('before', 'Antes de los Trabajos'),
        ('during', 'Durante los Trabajos'),
        ('after', 'Después de los Trabajos'),
        ('measurements', 'Medidas y Planos'),
        ('terrain', 'Estado del Terreno'),
        ('existing', 'Elementos Existentes'),
        ('access', 'Accesos y Espacios'),
        ('reference', 'Fotos de Referencia'),
        ('other', 'Otras'),
    ]
    
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='photographic_report',
        verbose_name="Cotizacion"
    )
    
    # Image and details
    image = models.ImageField(
        upload_to='quotations/photographic_report/',
        verbose_name="Imagen"
    )
    photo_type = models.CharField(
        max_length=20,
        choices=PHOTO_TYPE_CHOICES,
        default='before',
        verbose_name="Tipo de Foto"
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Titulo",
        help_text="Titulo descriptivo de la foto"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descripcion",
        help_text="Descripcion detallada de lo que muestra la foto"
    )
    
    # Technical details
    location_description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Ubicacion",
        help_text="Donde fue tomada la foto (ej: jardín trasero, entrada principal)"
    )
    photo_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de la Foto"
    )
    
    # Organization
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de aparicion en el reporte"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Foto de Reporte Fotografico"
        verbose_name_plural = "Fotos de Reporte Fotografico"
        ordering = ['photo_type', 'order', 'created_at']

    def __str__(self):
        type_display = dict(self.PHOTO_TYPE_CHOICES).get(self.photo_type, self.photo_type)
        title_part = f" - {self.title}" if self.title else ""
        return f"{self.quotation.quotation_number} - {type_display}{title_part}"

    @property
    def display_title(self):
        """Return title if provided, otherwise a default based on type and location"""
        if self.title:
            return self.title
        
        type_display = dict(self.PHOTO_TYPE_CHOICES).get(self.photo_type, 'Foto')
        location_part = f" - {self.location_description}" if self.location_description else ""
        return f"{type_display}{location_part}"


class QuotationItem(models.Model):
    """Individual items in a quotation"""
    
    quotation = models.ForeignKey(
        Quotation, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name="Cotizacion"
    )
    service = models.ForeignKey(
        Service, 
        on_delete=models.CASCADE,
        verbose_name="Servicio"
    )
    
    # Quantity and pricing
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Cantidad"
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Precio Unitario"
    )
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name="Tasa de Impuesto (%)"
    )
    
    # Custom description (can override service description)
    description = models.TextField(
        blank=True,
        verbose_name="Descripcion Personalizada",
        help_text="Deja en blanco para usar la descripcion del servicio"
    )
    
    # Custom image for this specific quotation item
    custom_image = models.ImageField(
        upload_to='quotations/items/',
        blank=True,
        null=True,
        verbose_name="Imagen Personalizada",
        help_text="Imagen especifica para esta cotizacion (opcional, usa la del servicio si esta vacia)"
    )
    
    # Order for display
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Item de Cotizacion"
        verbose_name_plural = "Items de Cotizacion"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.service.name}"

    def save(self, *args, **kwargs):
        # Auto-populate price and tax rate from service if not set
        if not self.unit_price:
            self.unit_price = self.service.unit_price
        if not self.tax_rate:
            self.tax_rate = self.service.tax_rate
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        """Calculate subtotal for this item"""
        return self.quantity * self.unit_price

    @property
    def tax_amount(self):
        """Calculate tax amount for this item"""
        return self.subtotal * (self.tax_rate / Decimal('100'))

    @property
    def total_amount(self):
        """Calculate total amount for this item (including tax)"""
        return self.subtotal + self.tax_amount

    @property
    def display_description(self):
        """Return custom description if provided, otherwise service description"""
        return self.description if self.description else self.service.description

    @property
    def display_image(self):
        """Return custom image if provided, otherwise service main image"""
        if self.custom_image:
            return self.custom_image
        elif self.service.main_image:
            return self.service.main_image
        return None

    def get_all_images(self):
        """Get all available images for this item (custom + service gallery)"""
        images = []
        
        # Add custom image if exists
        if self.custom_image:
            images.append({
                'image': self.custom_image,
                'caption': 'Imagen personalizada',
                'is_custom': True
            })
        
        # Add service main image if exists and no custom image
        elif self.service.main_image:
            images.append({
                'image': self.service.main_image,
                'caption': 'Imagen principal del servicio',
                'is_custom': False
            })
        
        # Add service gallery images
        for gallery_image in self.service.gallery_images.all():
            images.append({
                'image': gallery_image.image,
                'caption': gallery_image.caption or f'Imagen del servicio',
                'is_custom': False
            })
        
        return images


class QuotationItemImage(models.Model):
    """Additional images for specific quotation items"""
    
    quotation_item = models.ForeignKey(
        QuotationItem,
        on_delete=models.CASCADE,
        related_name='additional_images',
        verbose_name="Item de Cotizacion"
    )
    image = models.ImageField(
        upload_to='quotations/items/gallery/',
        verbose_name="Imagen"
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Descripcion",
        help_text="Descripcion de la imagen"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Imagen Adicional de Item"
        verbose_name_plural = "Imagenes Adicionales de Items"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.quotation_item} - Imagen {self.order}"

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from ordered_model.models import OrderedModel


class ServiceCategory(models.Model):
    """Categories for services"""
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoria de Servicio"
        verbose_name_plural = "Categorias de Servicios"
        ordering = ['name']

    def __str__(self):
        return self.name


class Service(models.Model):
    """Model to represent services/products that can be quoted"""
    
    UNIT_CHOICES = [
        ('lote', 'Lote'),
        ('m2', 'Metro cuadrado'),
        ('m3', 'Metro cúbico'),
        ('unidad', 'Unidad'),
        ('ml', 'Metro lineal'),
        ('kg', 'Kilogramo'),
        ('hora', 'Hora'),
        ('dia', 'Día'),
        ('servicio', 'Servicio'),
    ]
    
    # Basic information
    name = models.CharField(max_length=200, verbose_name="Nombre del Servicio")
    description = models.TextField(verbose_name="Descripción")
    category = models.ForeignKey(
        ServiceCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Categoria"
    )
    
    # Main image for the service
    main_image = models.ImageField(
        upload_to='services/images/',
        blank=True,
        null=True,
        verbose_name="Imagen Principal",
        help_text="Imagen principal que aparecerá en las cotizaciones"
    )
    
    # Pricing
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio Unitario"
    )
    unit = models.CharField(
        max_length=20, 
        choices=UNIT_CHOICES, 
        default='unidad',
        verbose_name="Unidad"
    )
    
    # Tax information
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=16.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Tasa de Impuesto (%)",
        help_text="Ejemplo: 16.00 para 16% de IVA"
    )
    
    # Additional information
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    # Status and timestamps
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ['category__name', 'name']

    def __str__(self):
        return f"{self.name} - ${self.unit_price:.2f}/{self.unit}"

    def get_price_with_tax(self, quantity=1):
        """Calculate price including tax for given quantity"""
        subtotal = self.unit_price * Decimal(str(quantity))
        tax_amount = subtotal * (self.tax_rate / Decimal('100'))
        return subtotal + tax_amount

    def get_tax_amount(self, quantity=1):
        """Calculate tax amount for given quantity"""
        subtotal = self.unit_price * Decimal(str(quantity))
        return subtotal * (self.tax_rate / Decimal('100'))


class ServiceImage(OrderedModel):
    """Additional images for services (gallery)"""
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='gallery_images',
        verbose_name="Servicio"
    )
    image = models.ImageField(
        upload_to='services/gallery/',
        verbose_name="Imagen"
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Descripcion",
        help_text="Descripcion opcional de la imagen"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # OrderedModel configuration
    order_with_respect_to = 'service'

    class Meta(OrderedModel.Meta):
        verbose_name = "Imagen de Servicio"
        verbose_name_plural = "Imagenes de Servicios"

    def __str__(self):
        return f"{self.service.name} - Imagen {self.order}"

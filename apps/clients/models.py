from django.db import models
from django.core.validators import EmailValidator, RegexValidator


class Client(models.Model):
    """Model to represent clients/customers"""
    
    # Basic information
    name = models.CharField(max_length=200, verbose_name="Nombre")
    email = models.EmailField(
        validators=[EmailValidator()], 
        blank=True, 
        null=True,
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
    
    # Address information
    street = models.CharField(max_length=255, verbose_name="Calle", blank=True)
    city = models.CharField(max_length=100, verbose_name="Ciudad", blank=True)
    state = models.CharField(max_length=100, verbose_name="Estado", blank=True)
    postal_code = models.CharField(max_length=10, verbose_name="Código Postal", blank=True)
    country = models.CharField(max_length=100, default="México", verbose_name="País")
    
    # Additional information
    notes = models.TextField(blank=True, verbose_name="Notas")
    photo = models.ImageField(
        upload_to='clients/photos/', 
        blank=True, 
        null=True, 
        verbose_name="Foto",
        help_text="Foto del cliente (opcional)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def full_address(self):
        """Return the complete address as a string"""
        address_parts = [
            self.street,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ", ".join([part for part in address_parts if part])

    def get_quotations_count(self):
        """Return the number of quotations for this client"""
        return self.quotations.count()

    get_quotations_count.short_description = "Cotizaciones"

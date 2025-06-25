from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.contrib.auth.models import User
from django.urls import reverse


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

    def get_notes_count(self):
        """Return the number of notes for this client"""
        return self.client_notes.count()

    get_notes_count.short_description = "Notas"


class ClientNote(models.Model):
    """Model to represent internal notes for clients"""
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    TYPE_CHOICES = [
        ('general', 'General'),
        ('follow_up', 'Seguimiento'),
        ('complaint', 'Queja'),
        ('compliment', 'Elogio'),
        ('payment', 'Pago'),
        ('technical', 'Técnica'),
        ('commercial', 'Comercial'),
    ]
    
    # Relationships
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='client_notes',
        verbose_name="Cliente"
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Autor"
    )
    
    # Note content
    title = models.CharField(max_length=200, verbose_name="Título")
    content = models.TextField(verbose_name="Contenido")
    note_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='general',
        verbose_name="Tipo de nota"
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium',
        verbose_name="Prioridad"
    )
    
    # Status and visibility
    is_private = models.BooleanField(
        default=False, 
        verbose_name="Nota privada",
        help_text="Solo visible para el autor"
    )
    is_resolved = models.BooleanField(
        default=False, 
        verbose_name="Resuelto",
        help_text="Marcar si la nota ha sido resuelta o atendida"
    )
    
    # Follow-up
    follow_up_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Fecha de seguimiento",
        help_text="Fecha para dar seguimiento a esta nota"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    resolved_at = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Fecha de resolución"
    )

    class Meta:
        verbose_name = "Nota del Cliente"
        verbose_name_plural = "Notas de Clientes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['priority', 'is_resolved']),
            models.Index(fields=['follow_up_date']),
        ]

    def __str__(self):
        return f"{self.client.name} - {self.title}"

    def get_absolute_url(self):
        return reverse('clients:note_detail', kwargs={'pk': self.pk})

    def get_priority_badge_class(self):
        """Return CSS class for priority badge"""
        priority_classes = {
            'low': 'badge-secondary',
            'medium': 'badge-info',
            'high': 'badge-warning',
            'urgent': 'badge-danger',
        }
        return priority_classes.get(self.priority, 'badge-secondary')

    def get_type_badge_class(self):
        """Return CSS class for type badge"""
        type_classes = {
            'general': 'badge-light',
            'follow_up': 'badge-primary',
            'complaint': 'badge-danger',
            'compliment': 'badge-success',
            'payment': 'badge-warning',
            'technical': 'badge-info',
            'commercial': 'badge-dark',
        }
        return type_classes.get(self.note_type, 'badge-light')

    def save(self, *args, **kwargs):
        # Auto-set resolved_at when marking as resolved
        if self.is_resolved and not self.resolved_at:
            from django.utils import timezone
            self.resolved_at = timezone.now()
        elif not self.is_resolved:
            self.resolved_at = None
        
        super().save(*args, **kwargs)

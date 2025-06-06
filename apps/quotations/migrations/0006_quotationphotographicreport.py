# Generated by Django 5.1.7 on 2025-06-05 23:22

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotations', '0005_alter_quotation_options_alter_quotationitem_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuotationPhotographicReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='quotations/photographic_report/', verbose_name='Imagen')),
                ('photo_type', models.CharField(choices=[('before', 'Antes de los Trabajos'), ('during', 'Durante los Trabajos'), ('after', 'Después de los Trabajos'), ('measurements', 'Medidas y Planos'), ('terrain', 'Estado del Terreno'), ('existing', 'Elementos Existentes'), ('access', 'Accesos y Espacios'), ('reference', 'Fotos de Referencia'), ('other', 'Otras')], default='before', max_length=20, verbose_name='Tipo de Foto')),
                ('title', models.CharField(blank=True, help_text='Titulo descriptivo de la foto', max_length=200, verbose_name='Titulo')),
                ('description', models.TextField(blank=True, help_text='Descripcion detallada de lo que muestra la foto', verbose_name='Descripcion')),
                ('location_description', models.CharField(blank=True, help_text='Donde fue tomada la foto (ej: jardín trasero, entrada principal)', max_length=200, verbose_name='Ubicacion')),
                ('photo_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Fecha de la Foto')),
                ('order', models.PositiveIntegerField(default=0, help_text='Orden de aparicion en el reporte', verbose_name='Orden')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quotation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photographic_report', to='quotations.quotation', verbose_name='Cotizacion')),
            ],
            options={
                'verbose_name': 'Foto de Reporte Fotografico',
                'verbose_name_plural': 'Fotos de Reporte Fotografico',
                'ordering': ['photo_type', 'order', 'created_at'],
            },
        ),
    ]

# Generated by Django 5.2.2 on 2025-06-22 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quotations', '0009_make_salesperson_required'),
    ]

    operations = [
        migrations.AlterField(
            model_name='quotation',
            name='terms_and_conditions',
            field=models.TextField(blank=True, help_text='Se llenarán automáticamente desde el perfil de la empresa', null=True, verbose_name='Términos y Condiciones'),
        ),
    ]

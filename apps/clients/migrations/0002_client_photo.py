# Generated by Django 5.2.2 on 2025-06-06 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='photo',
            field=models.ImageField(blank=True, help_text='Foto del cliente (opcional)', null=True, upload_to='clients/photos/', verbose_name='Foto'),
        ),
    ]

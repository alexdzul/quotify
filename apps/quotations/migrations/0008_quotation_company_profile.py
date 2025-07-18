# Generated by Django 5.2.2 on 2025-06-22 16:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_companyprofile_facebook_url_and_more'),
        ('quotations', '0007_quotationactivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='quotation',
            name='company_profile',
            field=models.ForeignKey(default=1, help_text='Perfil de empresa asociado a esta cotización', on_delete=django.db.models.deletion.PROTECT, related_name='quotations', to='core.companyprofile', verbose_name='Perfil de Empresa'),
            preserve_default=False,
        ),
    ]

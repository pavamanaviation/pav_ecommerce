# Generated by Django 5.1.6 on 2025-02-22 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pavaman_backend', '0005_remove_productdetails_cart_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='productdetails',
            name='cart_status',
            field=models.BooleanField(default=False),
        ),
    ]

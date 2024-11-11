# Generated by Django 5.1.3 on 2024-11-06 07:55

import django.core.validators
import django.db.models.functions.text
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active', max_length=8)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_delete', models.BooleanField(default=False)),
                ('offer_type', models.CharField(choices=[('none', 'No Offer'), ('percentage', 'Percentage'), ('fixed', 'Fixed Amount')], default='none', max_length=10)),
                ('offer_value', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('offer_start_date', models.DateTimeField(blank=True, null=True)),
                ('offer_end_date', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'constraints': [models.UniqueConstraint(django.db.models.functions.text.Lower('name'), name='unique_category_name_case_insensitive')],
            },
        ),
    ]

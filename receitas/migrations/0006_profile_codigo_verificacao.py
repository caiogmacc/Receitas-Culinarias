# Generated by Django 5.1.1 on 2024-10-16 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('receitas', '0005_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='codigo_verificacao',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]

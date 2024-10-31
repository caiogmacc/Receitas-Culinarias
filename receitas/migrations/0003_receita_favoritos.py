# Generated by Django 5.1.1 on 2024-10-10 19:06

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('receitas', '0002_avaliacao'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='receita',
            name='favoritos',
            field=models.ManyToManyField(blank=True, related_name='receitas_favoritas', to=settings.AUTH_USER_MODEL),
        ),
    ]

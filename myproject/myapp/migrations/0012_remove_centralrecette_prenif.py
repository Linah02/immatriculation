# Generated by Django 5.1.1 on 2024-10-28 09:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0011_logiciel_modepaiement_numimpot_centralrecette_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='centralrecette',
            name='prenif',
        ),
    ]

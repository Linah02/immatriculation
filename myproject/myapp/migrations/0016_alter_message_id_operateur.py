# Generated by Django 5.1.1 on 2024-11-12 07:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0015_operateurs_message'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='id_operateur',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.operateurs'),
        ),
    ]
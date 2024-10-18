# Generated by Django 5.1.1 on 2024-10-15 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0009_contribuable_bank_acct_no_contribuable_dm_ref_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Operateur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cin', models.CharField(max_length=15)),
                ('contact', models.CharField(max_length=14)),
            ],
        ),
        migrations.AlterField(
            model_name='contribuable',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
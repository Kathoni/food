# Generated by Django 5.1.7 on 2025-04-10 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='customer_name',
            field=models.CharField(default='Anonymous', max_length=100),
        ),
    ]

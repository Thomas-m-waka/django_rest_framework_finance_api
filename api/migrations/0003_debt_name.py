# Generated by Django 5.1.2 on 2024-10-28 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_debt_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='debt',
            name='name',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
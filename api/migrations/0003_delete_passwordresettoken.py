# Generated by Django 5.1.2 on 2024-10-19 17:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_profile_phone_number'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PasswordResetToken',
        ),
    ]

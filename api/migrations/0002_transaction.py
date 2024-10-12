# Generated by Django 5.1.2 on 2024-10-10 18:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('transaction_type', models.CharField(choices=[('income', 'Income'), ('expense', 'Expense')], max_length=7)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('mpesa', 'M-Pesa'), ('paypal', 'PayPal'), ('bank', 'Bank Transfer'), ('creditcard', 'Credit Card')], max_length=15)),
                ('category', models.CharField(choices=[('salary', 'Salary'), ('investments', 'Investments'), ('bills', 'Bills'), ('shopping', 'Shopping'), ('food', 'Food')], max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

# api/utils.py

from django.db.models import Sum
from .models import Transaction

def calculate_total_income(user):
    return Transaction.objects.filter(user=user, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0

def calculate_total_expenses(user):
    return Transaction.objects.filter(user=user, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0




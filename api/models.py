from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.conf import settings
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_auth_token(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Profile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('rather_not_say', 'Rather Not Say'),
    ]

    OCCUPATION_CHOICES = [
        ('engineer', 'Engineer'),
        ('doctor', 'Doctor'),
        ('software_dev', 'Software Developer'),
        ('teacher', 'Teacher'),
        ('lawyer', 'Lawyer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES)
    date_of_birth = models.DateField()



class Transaction(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('paypal', 'PayPal'),
        ('bank', 'Bank Transfer'),
        ('creditcard', 'Credit Card'),
    ]

    INCOME_CATEGORIES = [
        ('salary', 'Salary'),
        ('investments', 'Investments'),
    ]

    EXPENSE_CATEGORIES = [
        ('bills', 'Bills'),
        ('shopping', 'Shopping'),
        ('food', 'Food'),
    ]

    # Subcategories for Income
    INCOME_SUBCATEGORIES = {
        'salary': ['Monthly Salary', 'Bonus'],
        'investments': ['Stocks', 'Bonds'],
    }

    # Subcategories for Expenses
    EXPENSE_SUBCATEGORIES = {
        'bills': ['Electricity', 'Water', 'Internet'],
        'shopping': ['Groceries', 'Clothing', 'Electronics'],
        'food': ['Dining Out', 'Groceries'],
    }

    TRANSACTION_TYPE = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPE)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHODS)
    category = models.CharField(max_length=50, choices=INCOME_CATEGORIES + EXPENSE_CATEGORIES)

    def __str__(self):
        return f"{self.transaction_type.capitalize()}: {self.amount} on {self.date}"




class Debt(models.Model):
    DEBT_TYPES = [
        ('credit_card', 'Credit Card'),
        ('personal_loan', 'Personal Loan'),
        ('mortgage', 'Mortgage'),
        ('student_loan', 'Student Loan'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='debts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    debt_type = models.CharField(max_length=50, choices=DEBT_TYPES)

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.debt_type})"
    
 

def get_total_debt(user):
    return Debt.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum'] or 0





class DebtRepayment(models.Model):
    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('mpesa', 'M-Pesa'),
        ('other', 'Other'),
    ]

    debt = models.ForeignKey(Debt, on_delete=models.CASCADE, related_name='repayments')
    date = models.DateField(auto_now=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODES)

    def __str__(self):
        return f"Repayment of {self.amount} for {self.debt} on {self.date}"


class FinancialGoal(models.Model):
    GOAL_TYPES = [
        ('basic', 'Basic (e.g., House)'),
        ('luxury', 'Luxury (e.g., Car)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_goals')
    amount_needed = models.DecimalField(max_digits=10, decimal_places=2)
    duration_weeks = models.PositiveIntegerField()
    description = models.CharField(max_length=255)
    goal_type = models.CharField(max_length=10, choices=GOAL_TYPES)

    def __str__(self):
        return f"{self.description} - {self.amount_needed} over {self.duration_weeks} weeks"
    

class PasswordResetToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    verification_code = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password reset token for {self.user.username}"
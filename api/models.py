from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.conf import settings
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField


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
    phone_number = PhoneNumberField(blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    occupation = models.CharField(max_length=20, choices=OCCUPATION_CHOICES)
    date_of_birth = models.DateField()


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('bank', 'Bank'),
        ('mpesa', 'M-Pesa'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ]

    BANKS = [
        ('kcb', 'KCB'),
        ('equity', 'Equity'),
        ('family', 'Family Bank'),
        ('worldbank', 'World Bank'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    account_number = models.CharField(max_length=20, unique=True)  # Unique account number
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES)
    bank_name = models.CharField(max_length=50, choices=BANKS, blank=True)  
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.account_type.capitalize()} - {self.bank_name or 'N/A'} (Account No: {self.account_number}, Amount: {self.amount})"

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
        ('Utilities', 'utilities'),
    ]

    TRANSACTION_TYPE = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions',null=True)
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPE)
    category = models.CharField(max_length=50, choices=INCOME_CATEGORIES + EXPENSE_CATEGORIES)
    description = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if self.transaction_type == 'expense' and self.amount > self.account.amount:
            raise ValueError("Insufficient funds in the selected account for this expense.")

        # Update account balance based on transaction type
        if self.transaction_type == 'income':
            self.account.amount += self.amount
        elif self.transaction_type == 'expense':
            self.account.amount -= self.amount

        # Save the account and transaction atomically
        with transaction.atomic():
            self.account.save()
            super().save(*args, **kwargs)

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
    STATUS_CHOICES = [
    ('active', 'Active'),
    ('paid', 'Paid'),
]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='debts')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    debt_type = models.CharField(max_length=50, choices=DEBT_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    date = models.DateField(auto_now=True,blank=True)
    name = models.CharField(max_length=100, unique=True, blank=True)

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
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='debt_repayments')
    date = models.DateField(auto_now=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='debt_repayments')

    def save(self, *args, **kwargs):
        
        if self.debt.user != self.user:
            raise ValueError("You cannot pay off someone else's debt.")

        
        if self.amount > self.account.amount:
            raise ValueError("Insufficient funds in the selected account.")

        
        self.account.amount -= self.amount
        self.account.save()

        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Repayment of {self.amount} for {self.debt.name} on {self.date}"


class FinancialGoal(models.Model):
    GOAL_TYPES = [
        ('basic', 'Basic (e.g., House)'),
        ('luxury', 'Luxury (e.g., Car)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_goals')
    amount_needed = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    duration_weeks = models.PositiveIntegerField()
    description = models.CharField(max_length=255)
    goal_type = models.CharField(max_length=10, choices=GOAL_TYPES)

    def __str__(self):
        return f"{self.description} - {self.amount_needed} over {self.duration_weeks} weeks"
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from  .serializers import *
from  datetime import date
from rest_framework import serializers
from django.db import IntegrityError
from django.urls import reverse

class AccountSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ['id', 'account_number', 'account_type', 'bank_name', 'amount', 'user', 'url']
        read_only_fields = ['user']

    def create(self, validated_data):
        user = validated_data['user']  

        try:
            account = Account.objects.create(**validated_data)
            return account
        except IntegrityError:
            raise serializers.ValidationError("You already have an account of this type.")

    def get_url(self, obj):
        request = self.context.get('request')
        url = request.build_absolute_uri(reverse('account-detail', kwargs={'pk': obj.pk}))
        return url



class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone_number', 'gender', 'occupation', 'date_of_birth']
        read_only_fields = ['user']
    
    def validate_phone_number(self, value):
        if Profile.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        
        return value

    def validate_date_of_birth(self, value):
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be greater than today's date.")
        return value        

class RegistrationSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'profile']
        read_only_fields = ['user']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()  
        Profile.objects.create(user=user, **profile_data)  
        return user  
    
    def validate_profile(self, value):
        self.validate_date_of_birth(value.get('date_of_birth'))
        return value

    def validate_date_of_birth(self, value):
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be greater than today's date.")
        return value    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ['id','user']


class TotalBalanceSerializer(serializers.Serializer):
    total_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    read_only_fields = ['user']

class TransactionSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(write_only=True)

    class Meta:
        model = Transaction
        fields = ['account_number', 'amount', 'transaction_type', 'category', 'description']

    def validate(self, data):
        print(data)
        if data['transaction_type'] == 'income' and data['category'] not in dict(Transaction.INCOME_CATEGORIES):
            print("Transactiontype income")
            raise serializers.ValidationError("Invalid category for income.")
        elif data['transaction_type'] == 'expense' and data['category'] not in dict(Transaction.EXPENSE_CATEGORIES):
            print("Transactiontype expense")
            
            raise serializers.ValidationError("Invalid category for expense.")
        
        
        try:
            account = Account.objects.get(account_number=data['account_number'], user=self.context['request'].user)
        except Account.DoesNotExist:
            print("Account not found ")
            
            raise serializers.ValidationError("Account not found for the user.")
        
        data['account'] = account

        return data

    def create(self, validated_data):
        account_number = validated_data.pop('account_number')

        
        transaction = Transaction.objects.create(**validated_data)

        return transaction







class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = '__all__'
        read_only_fields = ['user']
    def validate_debt(self, value):
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("You do not have permission to repay this debt.")
        return value        
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("The amount must be a positive integer.")
        return value

class DebtRepaymentSerializer(serializers.ModelSerializer):
    debt_name = serializers.CharField(write_only=True)  
    account_number = serializers.CharField(write_only=True)  

    class Meta:
        model = DebtRepayment
        fields = ['debt_name', 'account_number', 'amount', 'user']  

    def validate(self, data):
        user = self.context['request'].user
        
        try:
            debt = Debt.objects.get(name=data['debt_name'], user=user)
        except Debt.DoesNotExist:
            raise serializers.ValidationError("Debt not found for the user.")

        try:
            account = Account.objects.get(account_number=data['account_number'], user=user)
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account not found for the user.")

        
        if data['amount'] > account.amount:
            raise serializers.ValidationError("Insufficient funds in the selected account.")

        data['debt'] = debt
        data['account'] = account

        return data

    def create(self, validated_data):
        debt_name = validated_data.pop('debt_name')
        account_number = validated_data.pop('account_number')

        
        user = self.context['request'].user
        
        
        debt = Debt.objects.get(name=debt_name, user=user)
        account = Account.objects.get(account_number=account_number, user=user)

        
        repayment = DebtRepayment.objects.create(
            debt=debt,
            account=account,
            amount=validated_data['amount'],  
            user=user  
        )


        account.save()
        debt.amount -= validated_data['amount']
        debt.save()

        return repayment










    


class FinancialGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialGoal
        fields = '__all__'
        read_only_fields = ['user']
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("The amount must be a positive integer.")
        return value        
    

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        if len(value) < 8:  
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value
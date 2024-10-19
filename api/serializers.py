from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from  .serializers import *
from  datetime import date
from rest_framework import serializers


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ['user']



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
        read_only_fields = ['user']


class TotalBalanceSerializer(serializers.Serializer):
    total_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    read_only_fields = ['user']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'account', 'amount', 'transaction_type', 'category', 'date']
        read_only_fields = ['user', 'date']

    def validate(self, attrs):
        account = attrs.get('account')
        amount = attrs.get('amount')
        transaction_type = attrs.get('transaction_type')

        if transaction_type == 'expense' and amount > account.amount:
            raise serializers.ValidationError("Insufficient funds in the selected account for this expense.")

        return attrs



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
    class Meta:
        model = DebtRepayment
        fields = ['debt', 'account', 'amount']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user)

    def validate_account(self, value):
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("You can only use your own account for this repayment.")
        return value

    def validate(self, data):
        debt = data['debt']
        if not Debt.objects.filter(id=debt.id).exists():
            raise serializers.ValidationError("Debt does not exist.")

        
        if not Account.objects.filter(id=data['account'].id, user=self.context['request'].user).exists():
            raise serializers.ValidationError("You can only repay using your own account.")
        
        
        if data['amount'] > debt.amount:
            raise serializers.ValidationError("Repayment amount cannot exceed the remaining debt amount.")
        
        return data



    


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




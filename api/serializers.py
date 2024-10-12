from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile,Debt,DebtRepayment,FinancialGoal
from  datetime import date
from .models import Transaction
from rest_framework import serializers


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone_number', 'gender', 'occupation', 'date_of_birth']
        read_only_fields = ['user']
    
    def validate_phone_number(self, value):
        if len(value) != 10 or not value.startswith('0'):
            raise serializers.ValidationError("Phone number must be 10 digits long and start with '0'.")
        
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
        user.save()  # Save user to the database
        Profile.objects.create(user=user, **profile_data)  # Create profile
        return user  # Return the user instance
    
    def validate_profile(self, value):
        # Validate the date of birth in the profile
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


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'user',  'amount', 'transaction_type', 'payment_method', 'category']
        read_only_fields = ['user']

    def create(self, validated_data):
        # Automatically assign the user from the request
        user = validated_data.pop('user')
        return Transaction.objects.create(user=user, **validated_data)

    def validate_amount(self, value):
        # Ensure the amount is a positive integer
        if value <= 0:
            raise serializers.ValidationError("The amount must be a positive integer.")
        return value    



class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = '__all__'
        read_only_fields = ['user']
    def validate_amount(self, value):
        # Ensure the amount is a positive integer
        if value <= 0:
            raise serializers.ValidationError("The amount must be a positive integer.")
        return value

class DebtRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtRepayment
        fields = '__all__'
        read_only_fields = ['user']

    def validate(self, attrs):
        debt = attrs['debt']
        amount = attrs['amount']

        # Ensure the amount is a positive integer
        if amount <= 0:
            raise serializers.ValidationError("The repayment amount must be a positive integer.")

        # Check if repayment amount exceeds the remaining debt amount
        if amount > debt.amount:
            raise serializers.ValidationError("Repayment amount cannot exceed the remaining debt amount.")
        
        return attrs

    


class FinancialGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialGoal
        fields = '__all__'
        read_only_fields = ['user']
    def validate_amount(self, value):
        # Ensure the amount is a positive integer
        if value <= 0:
            raise serializers.ValidationError("The amount must be a positive integer.")
        return value        
    



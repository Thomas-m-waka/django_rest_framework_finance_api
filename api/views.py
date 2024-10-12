from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from.serializers import *
from .serializers import RegistrationSerializer,TransactionSerializer,DebtSerializer,DebtRepaymentSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import Transaction,Debt,DebtRepayment
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db.models import Sum
from .utils import calculate_total_income, calculate_total_expenses
from rest_framework.exceptions import PermissionDenied


# api/views.py


class RegistrationView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # Save the user and return the user instance

        return Response({
            'user': {
                'username': user.username,
                'email': user.email,
            },
            'message': 'User registered successfully.'
        }, status=status.HTTP_201_CREATED)





class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            return Response({
                'message': 'Login successful',
                'user': {
                    'username': user.username,
                    'email': user.email,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Invalid username or password'
            }, status=status.HTTP_400_BAD_REQUEST)



class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to delete this transaction.")
        instance.delete()



class DebtListCreateView(generics.ListCreateAPIView):
    serializer_class = DebtSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Debt.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DebtRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DebtSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ensure that users can only access their own debts
        return Debt.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        # Check if the current user is the owner of the debt
        if instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to delete this debt.")
        instance.delete()

class TotalDebtView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_debt = Debt.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
        return Response({'total_debt': total_debt})
    
class DebtRepaymentListCreateView(generics.ListCreateAPIView):
    serializer_class = DebtRepaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DebtRepayment.objects.filter(debt__user=self.request.user)

    def perform_create(self, serializer):
        repayment = serializer.save()
        debt = repayment.debt

        # Update the debt amount
        debt.amount -= repayment.amount
        debt.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)




class FinancialSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_income = calculate_total_income(request.user)
        total_expenses = calculate_total_expenses(request.user)

        return Response({
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': total_income - total_expenses,
        })
    



class FinancialGoalListCreateView(generics.ListCreateAPIView):
    serializer_class = FinancialGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)

class FinancialGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FinancialGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to delete this financial goal.")
        instance.delete()



# from .models import PasswordResetToken  # Make sure to import your model
# from .serializers import VerifyCodeSerializer  # Import your serializer for code verification

# class VerifyVerificationCodeView(generics.GenericAPIView):
#     serializer_class = VerifyCodeSerializer

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = serializer.validated_data['user']  # Get the user from the serializer
#         verification_code = serializer.validated_data['verification_code']

#         # Verify the code
#         verified_user = verify_verification_code(user, verification_code)
#         if verified_user:
#             return Response({"detail": "Verification successful."}, status=status.HTTP_200_OK)
#         return Response({"detail": "Invalid or expired verification code."}, status=status.HTTP_400_BAD_REQUEST)



# import requests
# import json
# from django.conf import settings

# def send_sms(phone_number, message):
#     url = "https://sms.textsms.co.ke/api/services/sendsms"
#     payload = {
#         "mobile": f'+254{phone_number}',  # Ensure the phone number is in the correct format
#         "response_type": "json",
#         "partnerID": '10338',  # Your partner ID
#         "shortcode": 'TextSMS',  # Your shortcode
#         'apikey': settings.SMS_API_KEY,  # Store your API key in settings
#         "message": message
#     }
#     headers = {
#         'Content-Type': 'application/json'
#     }
    
#     try:
#         response = requests.post(url, headers=headers, data=json.dumps(payload))
#         response_data = response.json()
        
#         # Check for success
#         if response.status_code == 200 and response_data.get('status') == 'success':
#             return True  # SMS sent successfully
#         else:
#             # Log or handle failure response
#             print(f"Failed to send SMS: {response_data.get('message')}")
#             return False
#     except requests.exceptions.RequestException as e:
#         # Handle request exceptions
#         print(f"Error sending SMS: {str(e)}")
#         return False


# import random
# from django.utils import timezone

# def generate_verification_code():
#     # Generate a random 6-digit verification code
#     return random.randint(100000, 999999)

# def send_verification_code(user):
#     # Retrieve the user's profile
#     profile = get_object_or_404(Profile, user=user)
    
#     # Generate a verification code
#     verification_code = generate_verification_code()

#     # Save the verification code to the PasswordResetToken model
#     reset_token = PasswordResetToken.objects.create(
#         user=user,
#         verification_code=verification_code,
#         created_at=timezone.now()
#     )

#     # Send the verification code via SMS
#     message = f"Your verification code is: {verification_code}"
#     send_sms(profile.phone_number, message)

#     return reset_token

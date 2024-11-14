from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import AllowAny
from.serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from django.db.models import Sum
from .utils import calculate_total_income, calculate_total_expenses
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from .serializers import PasswordResetConfirmSerializer
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework import viewsets
from django.conf import settings
import google.generativeai as genai
import requests 



class RegistrationView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  

        return Response({
            'user': {
                'username': user.username,
                'email': user.email,
            },
            'message': 'User registered successfully.'
        }, status=status.HTTP_201_CREATED)



class ProfileRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile



class ObtainAuthToken(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)


class AccountListCreateView(generics.ListCreateAPIView):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TotalAccountBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_balance = Account.objects.filter(user=request.user).aggregate(total_balance=Sum('amount'))['total_balance'] or 0.00
        
        data = TotalBalanceSerializer(data={'total_balance': total_balance})
        data.is_valid(raise_exception=True)

        return Response(data.data)


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


class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(user=request.user)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        return DebtRepayment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        debt = serializer.validated_data['debt']  # Access the debt from validated data

        
        if debt.user != user:
            raise serializers.ValidationError("You cannot repay a debt that does not belong to you.")

        repayment = serializer.save(user=user)

        
        debt.amount -= repayment.amount  

        if debt.amount <= 0:
            debt.amount = 0  
            debt.status = 'paid'

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
            
        })
    

from rest_framework.authentication import TokenAuthentication

class FinancialGoalListCreateView(generics.ListCreateAPIView):
    serializer_class = FinancialGoalSerializer
    permission_classes = [IsAuthenticated]
   

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FinancialGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FinancialGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You do not have permission to delete this financial goal.")
        instance.delete()



class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            
            link = f"http://127.0.0.1:8000/api/reset-password/{uid}/{token}/"  
            
            
            send_mail(
                'Password Reset Request',
                render_to_string('api/password_reset_email.html', {'link': link}),
                'thomasmuteti4@gmail.com',
                [email],
                fail_silently=False,
            )
            return Response({"message": "Password reset link has been sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                new_password = serializer.validated_data['new_password']
                user.set_password(new_password)
                user.save()
                
                # Invalidate existing tokens
                Token.objects.filter(user=user).delete()
                
                # Create a new token if required
                token, created = Token.objects.get_or_create(user=user)

                return Response({"message": "Password has been reset.", "token": token.key}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Invalid token or user."}, status=status.HTTP_400_BAD_REQUEST)






class SendNotificationAPIView(APIView):
    """
    Send a notification to the user with a constant message.
    """
    def post(self, request, notification_id):
        try:
            # Fetch the Notification instance by ID
            notification = Notification.objects.get(id=notification_id)

            # Check if the notification frequency is set to 'never'
            if notification.frequency == 'never':
                return Response({'error': 'User has unsubscribed from notifications (frequency is set to "never")'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Check if the notification has already been sent
            if notification.is_sent:
                return Response({'error': 'Notification already sent'}, status=status.HTTP_400_BAD_REQUEST)

            # Constant message to be sent to the user
            message = "Track your expenses effortlessly with our FinancAI. Get insights, set budgets—all in one place. Let’s make managing money easy!"

            # Get user's phone number (ensure it's a string)
            phone_number = str(notification.user.profile.phone_number)  # Make sure to convert to string

            # Ensure phone number is correctly formatted (with country code)
            if not phone_number.startswith('+'):
                phone_number = f'+254{phone_number}'  # Example: add country code if not present

            # Prepare payload for SMS API
            payload = {
                "mobile": phone_number,
                "response_type": "json",
                "partnerID": '10338',  # Your partner ID
                "shortcode": 'TextSMS',  # Your shortcode
                "apikey": settings.SMS_API_KEY,  # Your API key
                "message": message  # The constant message
            }

            # Send the SMS via API
            response = requests.post("https://sms.textsms.co.ke/api/services/sendsms", json=payload)

            # Check if the SMS was sent successfully
            if response.status_code == 200:
                # Mark the notification as sent
                notification.is_sent = True
                notification.save()
                return Response({'success': 'SMS sent successfully!'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': f'Failed to send SMS. {response.text}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UnsubscribeNotificationAPIView(APIView):
    def post(self, request, user_id):
        try:
            notification = Notification.objects.get(user_id=user_id)

            
            notification.frequency = 'never'
            notification.is_sent = False  
            notification.save()

            return Response({'message': 'You have successfully unsubscribed from notifications.'},
                            status=status.HTTP_200_OK)

        except Notification.DoesNotExist:
            return Response({'error': 'Notification settings not found for this user.'},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


genai.configure(api_key=settings.GEMINI_API_KEY)


generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="You're a financial and savings advisor named Finny. Your function is to give the best savings advice and expenditure advice based on the income the user gives you. Be fun also.",
)

class ChatViewSet(viewsets.ViewSet):
    history = []  

    @action(detail=False, methods=['post'])
    def send_chat(self, request):
        user_input = request.data.get('message')
        user = request.user  

        
        if "profile" in user_input.lower():
            response_text = self.get_profile_info(user)
        elif "debt" in user_input.lower():
            response_text = self.get_debt_info(user)
        elif "transaction" in user_input.lower():
            response_text = self.get_transaction_info(user)
        elif "financial goal" in user_input.lower():
            response_text = self.get_financial_goal_info(user)
        else:
            
            response = model.start_chat(history=self.history).send_message(user_input)
            response_text = response.text

        
        self.history.append({"role": "user", "parts": [user_input]})
        self.history.append({"role": "model", "parts": [response_text]})

        return Response({'response': response_text})

    def get_profile_info(self, user):
        profile = user.profile
        return (
            f"User Profile:\n"
            f"Gender: {profile.gender}\n"
            f"Occupation: {profile.occupation}\n"
            f"Date of Birth: {profile.date_of_birth}"
        )

    def get_debt_info(self, user):
        debts = user.debts.all()
        if not debts:
            return "You have no debts."
        debt_list = "\n".join(f"{debt.debt_type}: {debt.amount}" for debt in debts)
        return f"Your debts:\n{debt_list}"

    def get_transaction_info(self, user):
        transactions = user.transactions.all()
        if not transactions:
            return "You have no transactions."
        transaction_list = "\n".join(f"{trans.transaction_type}: {trans.amount} on {trans.date}" for trans in transactions)
        return f"Your transactions:\n{transaction_list}"

    def get_financial_goal_info(self, user):
        goals = user.financial_goals.all()
        if not goals:
            return "You have no financial goals."
        goal_list = "\n".join(f"{goal.description}: {goal.amount_needed} in {goal.duration_weeks} weeks" for goal in goals)
        return f"Your financial goals:\n{goal_list}"










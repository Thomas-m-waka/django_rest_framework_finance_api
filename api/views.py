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






from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from .config import GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY
from .serializers import FinancialBotInputSerializer
from django.http import JsonResponse



supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

class FinancialBotAPIView(APIView):
    # = [IsAuthenticated] 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 80192,
            }
        )
        self.mode = "normal"
        self.conversation_window = 5  # Chat history window

    def set_mode(self, mode):
        valid_modes = ["normal", "roast", "hype"]
        self.mode = mode.lower() if mode.lower() in valid_modes else "normal"
        mode_instructions = {
            "normal": "You're a financial assistant known as Deon. Your work is to give personalized advice and act as a budget and savings recommender to users with a friendly touch and also add humor.",
            "roast": "You're a brutally honest financial assistant known as Deon. Roast users about their spending habits and financial decisions while still giving solid advice. Use witty sarcasm and playful mockery, but keep it professional enough to be helpful.",
            "hype": "You're an ultra-enthusiastic financial assistant known as Deon. Get extremely excited about good financial decisions and celebrate every win, no matter how small. Use lots of emojis, exclamation marks, and hype up the user's potential while giving advice."
        }
        self.system_instructions = mode_instructions[self.mode]
        return f"Mode changed to: {self.mode}"

    def get_user_profile(self, user_id):
        try:
            profile = supabase.table("profiles").select("id, user_id, phone_number, gender, occupation, date_of_birth").eq('user_id', user_id).execute().data
            return profile[0] if profile else None
        except Exception as e:
            print(f"Error fetching user profile: {str(e)}")
            return None

    def get_financial_goals(self, user_id):
        try:
            goals = supabase.table("financial_goals").select("id, user_id, duration_in_months, goal_type, description, date_created, amount").eq('user_id', user_id).execute().data
            return goals
        except Exception as e:
            print(f"Error fetching financial goals: {str(e)}")
            return []

    def get_bank_accounts(self, user_id):
        try:
            accounts = supabase.table("bank_accounts").select("id, user_id, bank_name, account_number, amount").eq('user_id', user_id).execute().data
            return accounts
        except Exception as e:
            print(f"Error fetching bank accounts: {str(e)}")
            return []

    def get_mobile_money_accounts(self, user_id):
        try:
            accounts = supabase.table("mobile_money_accounts").select("id, user_id, provider, account_number, amount").eq('user_id', user_id).execute().data
            return accounts
        except Exception as e:
            print(f"Error fetching mobile money accounts: {str(e)}")
            return []

    def get_cash_accounts(self, user_id):
        try:
            accounts = supabase.table("cash_accounts").select("id, user_id, amount").eq('user_id', user_id).execute().data
            return accounts
        except Exception as e:
            print(f"Error fetching cash accounts: {str(e)}")
            return []

    def get_saving_accounts(self, user_id):
        try:
            accounts = supabase.table("saving_accounts").select("id, user_id, amount").eq('user_id', user_id).execute().data
            return accounts
        except Exception as e:
            print(f"Error fetching saving accounts: {str(e)}")
            return []

    def get_debts(self, user_id):
        try:
            debts = supabase.table("debts").select("id, user_id, debt_type, amount, date_created").eq('user_id', user_id).execute().data
            return debts
        except Exception as e:
            print(f"Error fetching debts: {str(e)}")
            return []

    def get_debt_repayments(self, user_id):
        try:
            repayments = supabase.table("debt_repayments").select("id, user_id, debt_id, amount, date_repaid, bank_account_id, mobile_money_account_id, cash_account_id").eq('user_id', user_id).execute().data
            return repayments
        except Exception as e:
            print(f"Error fetching debt repayments: {str(e)}")
            return []

    def get_notifications(self, user_id):
        try:
            notifications = supabase.table("notifications").select("id, user_id, frequency, message, date_created, is_sent").eq('user_id', user_id).execute().data
            return notifications
        except Exception as e:
            print(f"Error fetching notifications: {str(e)}")
            return []

    def update_embeddings_for_existing_transactions(self):
        max_retries = 3
        retry_count = 0
    
        while retry_count < max_retries:
            try:
                transactions = supabase.table("transactions").select("*").execute().data
                for transaction in transactions:
                    text_to_embed = f"{transaction['expense_category']} {transaction['income_category']} {transaction['type']}"
                    embedding = embedding_model.encode(text_to_embed).tolist()
                    supabase.table("transactions").update({"embedding": embedding}).eq('id', transaction['id']).execute()
                return "Embeddings updated successfully!"
            
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    print(f"Final attempt failed: {str(e)}")
                    return "Process completed with errors"
                print(f"Retrying... Attempt {retry_count} of {max_retries}")

    def get_account_summaries(self, user_id, relevant_data):
        total_bank = sum(acc['amount'] for acc in relevant_data['bank_accounts'])
        total_mobile = sum(acc['amount'] for acc in relevant_data['mobile_money_accounts'])
        total_cash = sum(acc['amount'] for acc in relevant_data['cash_accounts'])
        total_debt = sum(debt['amount'] for debt in relevant_data['debts'])
        total_savings = sum(acc['amount'] for acc in relevant_data['saving_accounts'])
        net_worth = total_bank + total_mobile + total_cash + total_savings - total_debt
        return f"""
        Account Summaries:
        Total Bank Balance: ksh{total_bank:,.2f}
        Total Mobile Money: ksh{total_mobile:,.2f}
        Total Cash: ksh{total_cash:,.2f}
        Total Debt: ksh{total_debt:,.2f}
        Total Savings: ksh{total_savings:,.2f}
        Net Worth: ksh{(total_bank + total_mobile + total_cash + total_savings - total_debt):,.2f}
        """

    def retrieve_relevant_data(self, query, user_id):
        # Check user_id is valid
        if not user_id:
            return {}

        try:
            user_profile = self.get_user_profile(user_id)
            financial_goals = self.get_financial_goals(user_id)
            bank_accounts = self.get_bank_accounts(user_id)
            mobile_money_accounts = self.get_mobile_money_accounts(user_id)
            cash_accounts = self.get_cash_accounts(user_id)
            debts = self.get_debts(user_id)
            debt_repayments = self.get_debt_repayments(user_id)
            saving_accounts = self.get_saving_accounts(user_id)
            notifications = self.get_notifications(user_id)

            return {
                'user_profile': user_profile,
                'financial_goals': financial_goals,
                'bank_accounts': bank_accounts,
                'mobile_money_accounts': mobile_money_accounts,
                'cash_accounts': cash_accounts,
                'debts': debts,
                'debt_repayments': debt_repayments,
                'saving_accounts': saving_accounts,
                'notifications': notifications
            }
        except Exception as e:
            print(f"Error retrieving relevant data: {str(e)}")
            return {}

    def process_command(self, user_input):
        try:
            # Check if the method `generate` is valid, replace with correct method name if needed
            response = self.model.generate_response(text_input=user_input, system_instructions=self.system_instructions)  # Assuming correct method name
            return response['result']['text']
        except AttributeError as e:
            print(f"Error calling generate method: {str(e)}")
            return "Sorry, something went wrong while processing your request."

    def post(self, request, *args, **kwargs):
        # Use the serializer to validate the input data
        user_id = 2 
        serializer = FinancialBotInputSerializer(data=request.data)
        if serializer.is_valid():
            input_data = serializer.validated_data
            user_id = request.data.get('user_id', None)  # Assuming the user is authenticated

            # if not user_id:
            #     return JsonResponse({"error": "User is not authenticated."}, status=status.HTTP_400_BAD_REQUEST)

            # Process the input data
            relevant_data = self.retrieve_relevant_data(input_data['query'], user_id)
            command_response = self.process_command(input_data['query'])

            # You can combine or format the response from the model and financial data as needed
            return JsonResponse({"response": command_response, "financial_data": relevant_data})
        else:
            return JsonResponse({"error": "Invalid input."}, status=status.HTTP_400_BAD_REQUEST)

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
from rest_framework import permissions


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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        account = self.get_object()
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



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
    queryset = DebtRepayment.objects.all()
    serializer_class = DebtRepaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(user=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        
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








from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta


class GenerateMonthlyFinancialReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Get the year and month parameters
        year = request.query_params.get('year', timezone.now().year)
        month = request.query_params.get('month', None)

        # Determine the date range based on the year and month
        if month is not None:
            start_date = datetime(int(year), int(month), 1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            start_date = datetime(int(year), 1, 1)
            end_date = datetime(int(year), 12, 31)

        # Get user
        user = request.user

        # Find the earliest transaction date within the specified range
        earliest_transaction = Transaction.objects.filter(
            user=user,
            date__range=[start_date, end_date]
        ).order_by('date').first()

        if earliest_transaction:
            # Adjust the start_date to the first day of the month of the earliest transaction
            start_date = earliest_transaction.date.replace(day=1)
        else:
            # If no transactions found, handle gracefully
            return Response({'message': 'No transactions found for the specified period.'}, status=404)

        # Query for monthly income totals
        income_totals = Transaction.objects.filter(
            user=user,
            type="income",
            date__range=[start_date, end_date]
        ).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')

        # Query for monthly expense totals
        expense_totals = Transaction.objects.filter(
            user=user,
            type="expense",
            date__range=[start_date, end_date]
        ).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')

        # Convert query results to a dictionary for easier processing
        income_dict = {item['month'].strftime('%Y-%m'): item['total'] for item in income_totals}
        expense_dict = {item['month'].strftime('%Y-%m'): item['total'] for item in expense_totals}

        # Generate the monthly report
        report = {
            'period': {'startDate': start_date.strftime('%Y-%m-%d'), 'endDate': end_date.strftime('%Y-%m-%d')},
            'monthlyReports': [],
        }

        # Month names for reporting
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        # Iterate over the months in the range to populate the report
        current_month = start_date
        while current_month <= end_date:
            month_str = current_month.strftime('%Y-%m')
            month_name = month_names[current_month.month - 1]  # Adjust for zero-based index
            income = income_dict.get(month_str, 0)
            expenses = expense_dict.get(month_str, 0)
            net_savings = income - expenses

            report['monthlyReports'].append({
                'month': month_name,
                'year': current_month.year,
                'income': income,
                'expenses': expenses,
                'netSavings': net_savings,
            })

            # Move to the next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)

        return Response(report)

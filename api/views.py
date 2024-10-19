from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import AllowAny
from.serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
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
            
            # Update the link to point to your local server
            link = f"http://127.0.0.1:8000/api/reset-password/{uid}/{token}/"  # Adjust this based on your URL pattern
            
            # Send email
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

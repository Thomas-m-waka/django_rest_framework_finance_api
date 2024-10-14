from django.urls import path
from .views import *
from .views import DebtRepaymentListCreateView,FinancialSummaryView
#from .views import RegistrationView,TransactionDetailView,TransactionListCreateView,LoginView,DebtListCreateView,TotalDebtView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),  
    #path('login/', LoginView.as_view(), name='login'),
    path('token/', ObtainAuthToken.as_view(), name='obtain_token'), #Tokens are  generated from login

    path('transactions/', TransactionListCreateView.as_view(), name='transaction_list_create'),  # List and create transactions
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction_detail'),
    path('view_transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('debts/', DebtListCreateView.as_view(), name='debt-list-create'),
    path('debts/<int:pk>/', DebtRetrieveUpdateDestroyView.as_view(), name='debt-detail'),

    path('total-debt/', TotalDebtView.as_view(), name='total-debt'),
    path('debt-repayments/', DebtRepaymentListCreateView.as_view(), name='debt-repayment-list-create'),
    path('financial-summary/', FinancialSummaryView.as_view(), name='financial-summary'),
    path('financial-goals/', FinancialGoalListCreateView.as_view(), name='financial-goal-list-create'),
    path('financial-goals/<int:pk>/', FinancialGoalDetailView.as_view(), name='financial-goal-detail'),

    # path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    # path('password-reset-confirm/', PasswordResetView.as_view(), name='password-reset-confirm'),
    # path('verify-code/', VerifyVerificationCodeView.as_view(), name='verify-code'),  # For code verification
]   




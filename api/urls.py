from django.urls import path
from .views import *
from .views import DebtRepaymentListCreateView,FinancialSummaryView
from .views import RegistrationView,TransactionDetailView,TransactionListCreateView,LoginView,DebtListCreateView,TotalDebtView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),  
    path('login/', LoginView.as_view(), name='login'),
    #path('token/', TokenObtainPairView.as_view(), name='token'),
    #path('token/refresh', TokenRefreshView.as_view(), name='refresh'),
    # path('bot/', BotView.as_view(), name='bot'),
    path('transactions/', TransactionListCreateView.as_view(), name='transaction_list_create'),  # List and create transactions
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction_detail'),
    
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




# api/urls.py

# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import (
#     RegistrationView,
#     LoginView,
#     TransactionViewSet,
#     DebtViewSet,
#     DebtRepaymentViewSet,
#     FinancialGoalViewSet,
#     FinancialSummaryView,
# )

# router = DefaultRouter()
# router.register(r'transactions', TransactionViewSet, basename='transaction')
# router.register(r'debts', DebtViewSet, basename='debt')
# router.register(r'debt-repayments', DebtRepaymentViewSet, basename='debt-repayment')
# router.register(r'financial-goals', FinancialGoalViewSet, basename='financial-goal')

# urlpatterns = [
#     path('register/', RegistrationView.as_view(), name='register'),
#     path('login/', LoginView.as_view(), name='login'),
#    # path('token/', TokenObtainPairView.as_view(), name='token'),
#    # path('token/refresh/', TokenRefreshView.as_view(), name='refresh'),
    
#     # Include the router URLs
#     path('', include(router.urls)),
#     path('financial-summary/', FinancialSummaryView.as_view(), name='financial-summary'),
# ]

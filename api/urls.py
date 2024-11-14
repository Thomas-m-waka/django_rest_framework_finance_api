from django.urls import path
from .views import *
from .views import DebtRepaymentListCreateView,FinancialSummaryView
from .views import PasswordResetView, PasswordResetConfirmView
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="FinancAI",
        default_version='v1',
        description="FinanceAI",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="thomasmmuteti4@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)



urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('send-notification/<int:notification_id>/', SendNotificationAPIView.as_view(), name='send-notification'),
    path('unsubscribe-notification/<int:user_id>/', UnsubscribeNotificationAPIView.as_view(), name='unsubscribe-notification'),
    path('profile-update/', ProfileRetrieveUpdateView.as_view(), name='profile-update'),
    path('profileview/', ProfileRetrieveUpdateView.as_view(), name='profile-detail'),
    path('reset-password/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),  
    path('token/', ObtainAuthToken.as_view(), name='obtain_token'), 
    path('accounts/', AccountListCreateView.as_view(), name='account-list-create'),
    path('total-account-balance/', TotalAccountBalanceView.as_view(), name='total-account-balance'),
    path('transactions/', TransactionListCreateView.as_view(), name='transaction_list_create'),
    path('transactions/<int:pk>/', TransactionDetailView.as_view(), name='transaction_detail'),
    path('view_transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('debts/', DebtListCreateView.as_view(), name='debt-list-create'),
    path('debts/<int:pk>/', DebtRetrieveUpdateDestroyView.as_view(), name='debt-detail'),
    path('total-debt/', TotalDebtView.as_view(), name='total-debt'),
    path('debt-repayments/', DebtRepaymentListCreateView.as_view(), name='debt-repayment-list-create'),
    path('financial-summary/', FinancialSummaryView.as_view(), name='financial-summary'),
    path('financial-goals/', FinancialGoalListCreateView.as_view(), name='financial-goal-list-create'),
    path('financial-goals/<int:pk>/', FinancialGoalDetailView.as_view(), name='financial-goal-detail'),
    path('chat/send_chat/', ChatViewSet.as_view({'post': 'send_chat'}), name='chatbot'),  
   



    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
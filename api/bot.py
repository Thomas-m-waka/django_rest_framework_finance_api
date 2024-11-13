from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from config import GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY
from .serializers import FinancialBotInputSerializer
from django.http import JsonResponse


# Initialize Supabase client and SentenceTransformer
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


class FinancialBotAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access

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
        response = self.model.generate(text_input=user_input, system_instructions=self.system_instructions)
        return response['result']['text']

    def post(self, request, *args, **kwargs):
        # Use the serializer to validate the input data
        serializer = FinancialBotInputSerializer(data=request.data)
        if serializer.is_valid():
            input_data = serializer.validated_data
            user_id = request.user.id  # Assuming the user is authenticated

            # Process the input data
            relevant_data = self.retrieve_relevant_data(input_data['query'], user_id)
            command_response = self.process_command(input_data['query'])
            account_summary = self.get_account_summaries(user_id, relevant_data)

            result = {
                "relevant_data": relevant_data,
                "command_response": command_response,
                "account_summary": account_summary
            }
            return JsonResponse(result, status=status.HTTP_200_OK)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




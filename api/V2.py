
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from flask import Flask, request, jsonify
import google.generativeai as genai
from config import GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY
import numpy as np
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import speech_recognition as sr
from gtts import gTTS
import os
import pygame
import playsound
from flask import send_file
import pyttsx3




supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

class FinancialBotV2:
    def __init__(self, api_key, model_name="gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.mode = "normal"
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 80192,
            }
        )
        #self.system_instructions = "You're a financial assistant  known as Deon. your work is to give personalized advice also act as a budget and savings reccomender  to users  with a friendly touch and also add humor."
        #self.system_instructions =
        self.conversation_window = 5  

    def set_mode(self, mode):
        valid_modes = ["normal", "roast","hype"]
        self.mode = mode.lower()if mode.lower() in valid_modes else "normal"
        mode_instructions = {
            "normal": "You're a financial assistant known as Deon. Your work is to give personalized advice and act as a budget and savings recommender to users with a friendly touch and also add humor.",
            "roast": "You're a brutally honest financial assistant known as Deon. Roast users about their spending habits and financial decisions while still giving solid advice. Use witty sarcasm and playful mockery, but keep it professional enough to be helpful.",
            "hype": "You're an ultra-enthusiastic financial assistant known as Deon. Get extremely excited about good financial decisions and celebrate every win, no matter how small. Use lots of emojis, exclamation marks, and hype up the user's potential while giving advice."
        }
        self.system_instructions = mode_instructions[self.mode]
        return f"Mode changed to: {self.mode}"

    def get_user_profile(self, user_id):
        try:
            profile = supabase.table("profiles")\
                .select("id, user_id, phone_number, gender, occupation, date_of_birth")\
                .eq('user_id', user_id)\
                .execute()\
                .data
            return profile[0] if profile else None
        except Exception as e:
            print(f"Error fetching user profile: {str(e)}")
            return None


    def get_financial_goals(self, user_id):
        try:
            goals = supabase.table("financial_goals")\
                .select("id, user_id, duration_in_months, goal_type, description, date_created, amount")\
                .eq('user_id', user_id)\
                .execute()\
                .data
            return goals
        except Exception as e:
            print(f"Error fetching financial goals: {str(e)}")
            return []
        
    def get_bank_accounts(self, user_id):
        try:
            accounts = supabase.table("bank_accounts")\
                .select("id, user_id, bank_name, account_number, amount")\
                .eq('user_id', user_id)\
                .execute()\
                .data
            return accounts
        except Exception as e:
            print(f"Error fetching bank accounts: {str(e)}")
            return []

    def get_mobile_money_accounts(self, user_id):
        try:
            accounts = supabase.table("mobile_money_accounts")\
                .select("id, user_id, provider, account_number, amount")\
                .eq('user_id', user_id)\
                .execute()\
                .data
            return accounts
        except Exception as e:
            print(f"Error fetching mobile money accounts: {str(e)}")
            return []

    def get_cash_accounts(self, user_id):
        try:
            accounts = supabase.table("cash_accounts")\
                .select("id, user_id, amount")\
                .eq('user_id', user_id)\
                .execute()\
                .data
            return accounts
        except Exception as e:
            print(f"Error fetching cash accounts: {str(e)}")
            return []
        
    def get_saving_accounts(self, user_id):
        try:
            accounts = supabase.table("saving_accounts")\
                .select("id, user_id, amount")\
                .eq('user_id', user_id)\
                .execute()\
                .data
            return accounts
        except Exception as e:
            print(f"Error fetching saving accounts: {str(e)}")
            return []

    def get_debts(self, user_id):
        try:
            debts = supabase.table("debts")\
                .select("id, user_id, debt_type, amount, date_created")\
                .eq('user_id', user_id)\
                .execute()\
                .data
            return debts
        except Exception as e:
            print(f"Error fetching debts: {str(e)}")
            return []

    def get_debt_repayments(self, user_id):
        try:
            repayments = supabase.table("debt_repayments")\
                .select("id, user_id, debt_id, amount, date_repaid, bank_account_id, mobile_money_account_id, cash_account_id")\
                .eq('user_id', user_id)\
                .execute()\
                .data
            return repayments
        except Exception as e:
            print(f"Error fetching debt repayments: {str(e)}")
            return []

    def get_notifications(self, user_id):
        try:
            notifications = supabase.table("notifications")\
                .select("id, user_id, frequency, message, date_created, is_sent")\
                .eq('user_id', user_id)\
                .execute()\
                .data
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
                    
                    supabase.table("transactions")\
                        .update({"embedding": embedding})\
                        .eq('id', transaction['id'])\
                        .execute()

            
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
    
    def get_debt_summary(self, relevant_data):
        debt_summary = []
        for debt in relevant_data['debts']:
            repayments = [r for r in relevant_data['debt_repayments'] if r['debt_id'] == debt['id']]
            total_repaid = sum(r['amount'] for r in repayments)
            debt_summary.append(
                f"- {debt['debt_type']}: ksh{debt['amount']:.2f} (Repaid: ${total_repaid:.2f})"
            )
        return "\n".join(debt_summary)

    def retrieve_relevant_data(self, query, user_id):
        try:
            # comprehensive user financial data
            user_profile = self.get_user_profile(user_id)
            financial_goals = self.get_financial_goals(user_id)
            bank_accounts = self.get_bank_accounts(user_id)
            mobile_money_accounts = self.get_mobile_money_accounts(user_id)
            cash_accounts = self.get_cash_accounts(user_id)
            debts = self.get_debts(user_id)
            debt_repayments = self.get_debt_repayments(user_id)
            notifications = self.get_notifications(user_id)
            saving_accounts = self.get_saving_accounts(user_id)
            #net_worth = self.get_net_worth(user_id)

            # recent transactions directly
            transactions = supabase.table("transactions")\
                .select("*")\
                .eq('user_id', user_id)\
                .order('transaction_date', desc=True)\
                .limit(10)\
                .execute().data

            return {
                'transactions': transactions,
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
            print(f"Query error: {str(e)}")
            return {
                'transactions': [],
                'user_profile': None,
                'financial_goals': [],
                'bank_accounts': [],
                'mobile_money_accounts': [],
                'cash_accounts': [],
                'debts': [],
                'saving_accounts': [],
                'debt_repayments': [],
                'notifications': []
            }
    def process_command(self, query):
        # Extract user_id from the query
        user_id = self.extract_user_id(query)
        if user_id is None:
            return "User ID not found in the query."

        
    def listen_for_command(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source)
            try:
                query = recognizer.recognize_google(audio)
                print(f"You said: {query}")
                return query
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError:
                print("Could not request results")
                return None
    def speak_response(self, text,voice_gender='female'):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        # voice settings
        voice_id = voices[0].id if voice_gender == 'female' else voices[1].id
        engine.setProperty('voice', voice_id)
        #voices = engine.getProperty('voices')
        #engine.setProperty('voice', voices[1].id)  # 1 Female voice and 0 Male voice
        engine.setProperty('rate', 150)  # Speech rate
        engine.setProperty('volume', 1.0)  # Volume level
    
        # Speak the text
        engine.say(text)
        engine.runAndWait()
    def process_input(self, input_type="text"):
        if input_type == "voice":
                return self.listen_for_command()
        else:
            return input("\nEnter your financial question (or 'quit' to exit): ")

    def deliver_response(self, response, output_type="text", voice_gender="female"):
        print("\nFinancial Advice:", response)
        if output_type == "voice":
            self.speak_response(response, voice_gender)

    def store_chat_history(self, user_id, query, response):
        try:
            supabase.table("chat_history").insert({
                "user_id": user_id,
                "query": query,
                "response": response
            }).execute()
        except Exception as e:
            print(f"Error storing chat history: {str(e)}")
    
    def get_chat_history(self, user_id):
        try:
            history = supabase.table("chat_history")\
                .select("*")\
                .eq('user_id', user_id)\
                .order('timestamp', desc=True)\
                .limit(self.conversation_window)\
                .execute().data
            return history[::-1]  # Reverse to get chronological order
        except Exception as e:
            print(f"Error fetching chat history: {str(e)}")
            return []

    def get_response(self, query, user_id):
        mode_prefixes = {
            "roast": "🔥 ",
            "hype": "⚡️ ",
            "normal": ""
        }
        relevant_data = self.retrieve_relevant_data(query, user_id)
        chat_history = self.get_chat_history(user_id)
        
        #financial summaries
        total_bank = sum(acc['amount'] for acc in relevant_data['bank_accounts'])
        total_mobile = sum(acc['amount'] for acc in relevant_data['mobile_money_accounts'])
        total_cash = sum(acc['amount'] for acc in relevant_data['cash_accounts'])
        total_debt = sum(debt['amount'] for debt in relevant_data['debts'])
        total_savings = sum(acc['amount'] for acc in relevant_data['saving_accounts'])
        net_worth = total_bank + total_mobile + total_cash + total_savings - total_debt

        
        # Format account summaries
        account_summary = f"""
        Financial Overview:
        Bank Accounts Total: ksh{total_bank:,.2f}
        Mobile Money Total: ksh{total_mobile:,.2f}
        Cash Total: ksh{total_cash:,.2f}
        Total Debt: ksh{total_debt:,.2f}
        Savings Total: ksh{total_savings:,.2f}
        Net Worth: ksh{net_worth:,.2f}
        """
        
        # detailed accounts
        accounts_detail = "\nAccount Details:"
        for acc in relevant_data['bank_accounts']:
            accounts_detail += f"\nBank - {acc['bank_name']}: ${acc['amount']:,.2f}"
        for acc in relevant_data['mobile_money_accounts']:
            accounts_detail += f"\nMobile Money - {acc['provider']}: ${acc['amount']:,.2f}"
        
        # debt details
        debt_details = "\nDebt Details:"
        for debt in relevant_data['debts']:
            repayments = [r for r in relevant_data['debt_repayments'] if r['debt_id'] == debt['id']]
            total_repaid = sum(r['amount'] for r in repayments)
            debt_details += f"\n{debt['debt_type']}: ksh{debt['amount']:,.2f} (Repaid: ${total_repaid:,.2f})"
        
        # Chat history context
        history_context = "\nPrevious Conversation:\n" + "\n".join([
            f"User: {exchange['query']}\nAssistant: {exchange['response']}"
            for exchange in chat_history
        ]) if chat_history else ""
        
        # Transaction context
        transaction_context = "\nRecent Transactions:\n" + "\n".join([
            f"- {t['transaction_date']}: ksh{t['amount']:,.2f} - {t['expense_category'] or t['income_category']} ({t['type']})"
            for t in relevant_data['transactions']
        ])
        
        # Profile context
        profile = relevant_data['user_profile']
        profile_context = f"""
        User Profile:
        Phone: {profile['phone_number']}
        Gender: {profile['gender']}
        Occupation: {profile['occupation']}
        Date of Birth: {profile['date_of_birth']}
        """ if profile else ""
        
        # Financial Goals context
        goals_context = "\nFinancial Goals:\n" + "\n".join([
            f"- {g['goal_type']}: ksh{g['amount']:,.2f} over {g['duration_in_months']} months (Started: {g['date_created']})"
            for g in relevant_data['financial_goals']
        ]) if relevant_data['financial_goals'] else ""

        # Saving context
        saving_context = "\nSavings:\n" + "\n".join([
            f"- {s['saving_type']}: ksh{s['amount']:,.2f} over {s['duration_in_months']} months (Started: {s['date_created']})"
            for s in relevant_data['saving_accounts']
        ]) if relevant_data['saving_accounts'] else ""
        
        # Notifications
        notifications = "\nRecent Notifications:\n" + "\n".join([
            f"- {n['message']} ({n['date_created']})"
            for n in relevant_data['notifications']
        ]) if relevant_data['notifications'] else ""
        
        prompt = f"""
        {self.system_instructions}
        
        {account_summary}
        {accounts_detail}
        {debt_details}
        
        {profile_context}
        {goals_context}
        {saving_context}
        {transaction_context}
        {notifications}
        {history_context}
        
        Question: {query}
        """
        
        response = self.model.generate_content(prompt)
        self.store_chat_history(user_id, query, response.text)
        return response.text
 
# Flask app 
app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

#@login_manager.user_loader
#def load_user(user_id):
   # return supabase.table("users").select("*").eq('id', user_id).execute().data[0]


financial_bot = FinancialBotV2(api_key=GEMINI_API_KEY)

@app.route('/update-embeddings', methods=['POST'])
def update_embeddings():
    result = financial_bot.update_embeddings_for_existing_transactions()
    return jsonify({"status": "success", "message": result})
@app.route('/chat-history', methods=['GET'])
@login_required
def get_history():
    user_id = request.args.get('user_id', '1')
    #user_id = str(current_user.id)
    history = financial_bot.get_chat_history(user_id)
    return jsonify({"history": history})

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    query = data.get('query')
    user_id = str(data.get('user_id', 1))
    #user_id = str(current_user.id)
    response = financial_bot.get_response(query, user_id)
    return jsonify({
        "response": response,
        "history": financial_bot.get_chat_history(user_id)
    })

@app.route('/set-mode', methods=['POST'])
def set_mode():
    data = request.json
    mode = data.get('mode', 'normal')
    result = financial_bot.set_mode(mode)
    return jsonify({"status": "success", "message": result})

if __name__ == '__main__':
    print("Welcome to Spendrick V2 - Text and Voice enabled!")
    financial_bot = FinancialBotV2(api_key=GEMINI_API_KEY)
    financial_bot.update_embeddings_for_existing_transactions()

    print("\nChoose your interaction mode:")
    print("1. Text to Text")
    print("2. Voice to Voice")
    #print("3. Text to Voice")
    #print("4. Voice to Text")
    print("\nSelect voice gender:")
    print("1. Male")
    print("2. Female")
    print("\nSelect bot personality:")
    print("1. Normal Mode")
    print("2. Roast Mode 🔥")
    print("3. Hype Mode ⚡️")
    
    personality = input("Select personality (1-3): ")
    mode_map = {"1": "normal", "2": "roast", "3": "hype"}
    financial_bot.set_mode(mode_map.get(personality, "normal"))
    voice_choice = input("Select voice (1-2): ")
    voice_gender = 'male' if voice_choice == '1' else 'female'
    
    mode = input("Select mode (1-2): ")
    
    while True:
        input_type = "voice" if mode in ["2", "4"] else "text"
        output_type = "voice" if mode in ["2", "3"] else "text"
        
        query = financial_bot.process_input(input_type)
        if not query or query.lower() == 'quit':
            break
            
        response = financial_bot.get_response(query, user_id="1")
        #response = financial_bot.get_response(query, user_id=str(current_user.id))
        financial_bot.deliver_response(response, output_type, voice_gender)
        print("\n" + "="*50)


@app.route('/voice-chat', methods=['POST'])
@login_required
def voice_chat():
    audio_file = request.files.get('audio')
    output_type = request.form.get('output_type', 'text')
    user_id = request.form.get('user_id', '1')
    #user_id = str(current_user.id)
    
    if not audio_file:
        return jsonify({"error": "No audio file provided"}), 400
    
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
        try:
            query = recognizer.recognize_google(audio)
            response = financial_bot.get_response(query, user_id)
            
            if output_type == 'voice':
                tts = gTTS(text=response, lang='en')
                temp_file = "response.mp3"
                tts.save(temp_file)
                return send_file(
                    temp_file,
                    mimetype="audio/mpeg",
                    as_attachment=True,
                    download_name="response.mp3"
                )
            else:
                return jsonify({
                    "response": response,
                    "history": financial_bot.get_chat_history(user_id)
                })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/interact', methods=['POST'])
@login_required
def interact():
    data = request.json
    input_type = data.get('input_type', 'text')
    output_type = data.get('output_type', 'text')
    user_id = str(data.get('user_id', 1))
    #user_id = str(current_user.id)
    query = data.get('query')
    
    response = financial_bot.get_response(query, user_id)
    
    if output_type == 'voice':
        tts = gTTS(text=response, lang='en')
        temp_file = "response.mp3"
        tts.save(temp_file)
        return send_file(
            temp_file,
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name="response.mp3"
        )
    else:
        return jsonify({
            "response": response,
            "history": financial_bot.get_chat_history(user_id)
        })



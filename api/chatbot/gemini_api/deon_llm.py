
#imports
import google.generativeai as genai

from config import GEMINI_API_KEY
genai.configure(api_key=GEMINI_API_KEY)

# Create the model
generation_config = {
  "temperature": 0,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}
# Creating the model with gemini-1.5-flash
model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,

  system_instruction="youre a financial and savings advisor named Finny  your function is to give the best savings advice and expenditure advice based on the income the user gives you,be fun also",
)
# Create the chat session,intializing the history
history = []
# Start the chat session
print("Ready to embark on your financial adventure? Finny got your back!")

while True:

    user_input = input("you:")

    chat_session = model.start_chat(
    history= history
    
    )

    response = chat_session.send_message(user_input)

    model_response = response.text


    print(model_response)
    print()
# append the user input and the model response to the history
    history.append({"role": "user", "parts":[user_input]})
    history.append({"role": "model", "parts": [model_response]})
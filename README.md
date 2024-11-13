# django_rest_framework_finance_api

Create A Virtual Environment 
python3 -m venv venv
activate the virtual environment 
source venv/bin/activate  
install the requirements in the requiremenets.txt  file 
pip install  -r requirements.txt 

runserver  while on the file // Make sure you  can seee the file(manage.py)

python3 manage.py runserver 

urls to  be connceted using react are in  api/urls.py file 

sudo systemctl status postgresql




curl -X POST http://localhost:8000/api/accounts/ \
-H "Authorization: Token a01f62ad50e3b6396af09169b66ec073162a8bb6" \
-H "Content-Type: application/json" \
-d '{
  "user": 1,  
  "account_number": "001",
  "account_type": "bank",
  "bank_name": "kcb",
  "amount": 1000.00
}'





(venv) victor@fedora:~/Documents/secondyear/projects/backend/django_rest_framework_finance_api$ curl -X POST http://localhost:8000/api/transactions/ \
-H "Authorization: Token a01f62ad50e3b6396af09169b66ec073162a8bb6" \
-H "Content-Type: application/json" \
-d '{
    "account_number": "001",
    "amount": 200.50,
    "transaction_type": "expense",  
    "category": "shopping", 
    "description": "Grocery shopping"
}'
{"amount":"200.50","transaction_type":"expense",


"category":"shopping","description":"Grocery shopping"}(venv) victor@fedora:~/Documents/secondyear/projects/backend/django_rest_framework_finance_api$ 




(venv) victor@fedora:~/Documents/secondyear/projects/backend/django_rest_framework_finance_api$ curl -X POST http://localhost:8000/api/debts/ \
-H "Authorization: Token a01f62ad50e3b6396af09169b66ec073162a8bb6" \
-H "Content-Type: application/json" \
-d '{
    "amount": 1500.00,
    "debt_type": "personal_loan",
    "status": "active",
    "name": "Car Loan"
}'
{"id":1,"amount":"1500.00","debt_type":"personal_loan","status":"active","date":"2024-10-29","name":"Car Loan","user":1}(venv) victor@fedora:~/Documents/secondyear/projects/backend/django_rest_framework_finance_api$ 






(venv) victor@fedora:~/Documents/secondyear/projects/backend/django_rest_framework_finance_api$ curl -X POST http://localhost:8000/api/debt-repayments/ \ork_finance_api$ curl -X POST http://localhost:8000/api/debt-repayments/ \
-H "Authorization: Token a01f62ad50e3b6396af09169b66ec073162a8bb6" \
-H "Content-Type: application/json" \
-d '{
  "debt_name": "Car Loan", 
  "account_number": "001",
  "amount": 50.00,
"user":1
}'
{"amount":"50.00","user":1}(venv) victor@fedora:~/Documents/secondyear/projects/backend/django_rest_framework_finance_api$ 
import requests
import json

data = {
    "age": 35,
    "gender": "Female",
    "employment": "Salaried",
    "income": 55000,
    "credit_score": 720,
    "loan_amount": 150000,
    "loan_purpose": "Personal",
    "existing_debt": 12000,
    "loan_tenure": 24,
    "repayment_history": 1.0,
    "region": "Urban",
    "interview_notes": "The applicant seemed very genuine and has a stable job with good references."
}

try:
    response = requests.post("http://localhost:8000/api/predict", json=data)
    print("Response:", response.status_code)
    print(response.json())
except Exception as e:
    print("Error:", e)

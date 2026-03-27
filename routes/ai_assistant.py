from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from auth import staff_required
import re
import requests

ai_bp = Blueprint('ai', __name__)

def sanitize_input(text):
    if not text:
        return ""
    return re.sub(re.compile('<.*?>'), '', str(text))

# ---------------- DIAGNOSE ROUTE ----------------

@ai_bp.route('/diagnose', methods=['POST'])
@staff_required
def diagnose():
    api_key = current_app.config.get('OPENROUTER_API_KEY')
    data = request.json or {}
    symptoms = sanitize_input(data.get('symptoms'))

    print("USER:", symptoms)

    if not symptoms:
        return jsonify({'success': False, 'error': 'No symptoms provided.'})

    if not api_key or api_key.strip() == '':
        print("API ERROR: Missing API key.")
        return jsonify({
            'success': True,
            'diagnosis': f"**(Offline Demo Mode)**\n\nDiagnosis based on '{symptoms}' → Possible sensor or airflow issue."
        })

    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
You are an expert master mechanic working in a Vehicle Service Management System.

Analyze these symptoms:
{symptoms}

Give:

* Diagnosis
* Suggested service
* Required parts

Keep answer short and professional (max 120 words).
"""

        payload = {
            "model": current_app.config.get('AI_MODEL', 'nvidia/nemotron-3-super-120b-a12b:free'),
            "messages": [
                { "role": "user", "content": prompt }
            ]
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        response_data = response.json()
        reply = response_data['choices'][0]['message']['content']
        print("API RESPONSE:", reply)

        return jsonify({'success': True, 'diagnosis': reply})

    except Exception as e:
        print("API ERROR:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Chatbot is currently unavailable'})


# ---------------- CHAT ROUTE ----------------

@ai_bp.route('/chat', methods=['POST'])
@staff_required
def chat():
    api_key = current_app.config.get('OPENROUTER_API_KEY')
    data = request.json or {}
    message = sanitize_input(data.get('message'))

    print("USER:", message)

    if not message:
        return jsonify({'success': False, 'error': 'No message provided.'})

    if not api_key or api_key.strip() == '':
        print("API ERROR: Missing API key.")
        return jsonify({
            'success': True,
            'reply': "**(Offline Mode)** I'm your virtual mechanic. Please configure API key."
        })

    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
You are a helpful garage AI assistant.

Answer clearly and shortly:
{message}
"""

        payload = {
            "model": current_app.config.get('AI_MODEL', 'nvidia/nemotron-3-super-120b-a12b:free'),
            "messages": [
                { "role": "user", "content": prompt }
            ]
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        response_data = response.json()
        reply = response_data['choices'][0]['message']['content']
        print("API RESPONSE:", reply)

        return jsonify({'success': True, 'reply': reply})

    except Exception as e:
        print("API ERROR:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Chatbot is currently unavailable'})

import requests
from flask import Flask, request, jsonify
from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set your Twilio account SID and auth token
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
gpt_token = os.getenv('GPT_TOKEN')
gpt_neo_api_endpoint = os.getenv('GPT_ENDPOINT')
max_tokens = int(os.getenv('MAX_TOKENS', 60)) 
prompt = os.getenv('PROMPT_MODEL')

# Set Twilio client
client = Client(account_sid, auth_token)

# Set flask app
app = Flask(__name__)

def generate_gpt_neo_response(message):
    headers = {
        'Authorization': 'Bearer ' + gpt_token,
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                "role": 'assistant',
                "content": prompt
            },
            {
                "role": "user",
                "content": message
            }
        ]
    }

    print('sending request to ai')

    response = requests.post(gpt_neo_api_endpoint, headers=headers, json=data)
    response_data = response.json()

    print(response_data)

    if 'choices' in response_data and len(response_data['choices']) > 0:
        content = response_data['choices'][0]['message']['content']
        print(content)
        return content
    else:
        return None

def send_message(conversationSid, body):
    try:
        message = client.conversations \
                        .v1 \
                        .conversations(conversationSid) \
                        .messages \
                        .create(author='system', body=body)

        return message.sid
    except Exception as e:
        print(f"Failed to send message: {str(e)}")
        return None

@app.route('/conversations/webhook', methods=['POST'])
def conversations_webhook():
    data = request.form.to_dict()
    conversationSid = data.get('ConversationSid')
    message_body = data.get('Body')

    # Generate a response using GPT-Neo
    gpt_response = generate_gpt_neo_response(message_body)

    if gpt_response:
        message_sid = send_message(conversationSid, gpt_response)
        if message_sid:
            return jsonify(success=True, message_sid=message_sid), 200
        else:
            print('Failed to send message')
            return jsonify(success=False, error='Failed to send message'), 500
    else:
        print('Failed to generate response')
        return jsonify(success=False, error='Failed to generate response'), 500


if __name__ == '__main__':
    app.run(port=3001)

import os
from flask import Flask, request
from dotenv import load_dotenv
from services.whatsapp_handler import handle_incoming_message

load_dotenv()

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Twilio WhatsApp webhook endpoint.
    Receives incoming WhatsApp messages and processes them.
    """
    try:
        # Get message details from Twilio
        incoming_msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '')

        if not incoming_msg:
            return '', 200

        # Process the message
        response = handle_incoming_message(incoming_msg, sender)

        return str(response), 200

    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        return '', 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development')

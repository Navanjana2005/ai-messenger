import os
import requests
import json
import logging
from mistralai import Mistral
import config
from speech_to_text import speech_recognition

# Configuration
MISTRAL_API_KEY = config.MISTRAL_API_KEY
#SERVER_URL = "https://ab41da32abe0.ngrok-free.app"
SERVER_URL = "http://localhost:5000"
logger = logging.getLogger(__name__)

# Session variables
current_user_token = None
current_user_id = None
current_username = None


def authenticate_user():
    """Handle user signup/login"""
    global current_user_token, current_user_id, current_username

    print("\n" + "=" * 50)
    print("[AUTH] AI Messenger - Authentication")
    print("=" * 50)

    choice = input(
        "\nChoose an option:\n1. Login\n2. Signup\n\nEnter choice (1 or 2): "
    ).strip()

    if choice == "2":
        return signup_user()
    else:
        return login_user()


def signup_user():
    """Register a new user"""
    global current_user_token, current_user_id, current_username

    print("\n[FORM] Create New Account")
    username = input("Enter username (min 3 characters): ").strip()
    password = input("Enter password (min 6 characters): ").strip()
    email = input("Enter email (optional, press Enter to skip): ").strip() or None

    try:
        payload = {"username": username, "password": password, "email": email}

        response = requests.post(f"{SERVER_URL}/signup", json=payload, timeout=10)

        if response.status_code == 201:
            print("[SUCCESS] Account created successfully!")
            logger.info(f"User {username} signed up successfully")
            # Auto login after signup
            return login_with_credentials(username, password)
        else:
            error_msg = response.json().get("error", "Signup failed")
            print(f"[ERROR] Signup failed: {error_msg}")
            logger.warning(f"Signup failed: {error_msg}")
            return False
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        logger.error(f"Signup error: {e}")
        return False


def login_user():
    """Login user"""
    global current_user_token, current_user_id, current_username

    print("\n[LOGIN] Login to Account")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    return login_with_credentials(username, password)


def login_with_credentials(username, password):
    """Authenticate with username and password"""
    global current_user_token, current_user_id, current_username

    try:
        payload = {"username": username, "password": password}

        response = requests.post(f"{SERVER_URL}/login", json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            current_user_token = data.get("token")
            current_user_id = data.get("user_id")
            current_username = data.get("username")

            print(f"\n[SUCCESS] Welcome {current_username}!")
            logger.info(f"User {username} logged in successfully")
            return True
        else:
            error_msg = response.json().get("error", "Login failed")
            print(f"[ERROR] Login failed: {error_msg}")
            logger.warning(f"Login failed for user {username}")
            return False
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        logger.error(f"Login error: {e}")
        return False


def extract_message_details(user_input):
    """Use Mistral AI to extract recipient and message from voice/text input"""

    try:
        with Mistral(api_key=MISTRAL_API_KEY) as mistral:
            prompt = f"""
            Extract the recipient name and the message from this command:
            "{user_input}"
            
            Respond ONLY in this exact JSON format:
            {{"recipient": "name", "message": "the actual message"}}
            
            Example: If input is "Tell Jone to come at 4 pm today."
            Output: {{"recipient": "Jone", "message": "come at 4 pm today."}}
            """

            res = mistral.chat.complete(
                model="mistral-small-latest",
                messages=[{"content": prompt, "role": "user"}],
                stream=False,
            )

            # Extract the AI response
            ai_response = res.choices[0].message.content
            return ai_response
    except Exception as e:
        logger.error(f"AI extraction error: {e}")
        print(f"❌ Error processing with AI: {e}")
        return None


def send_message_to_server(recipient, message):
    """Send the extracted message to the server with authentication"""

    payload = {"token": current_user_token, "recipient": recipient, "message": message}

    try:
        response = requests.post(f"{SERVER_URL}/send_message", json=payload, timeout=10)
        if response.status_code == 200:
            print("[SUCCESS] Message sent successfully!")
            logger.info(f"Message sent from {current_username} to {recipient}")
            return True
        else:
            error_msg = response.json().get("error", "Failed to send message")
            print(f"[ERROR] Error: {error_msg}")
            logger.warning(f"Failed to send message: {error_msg}")
            return False
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        logger.error(f"Send message error: {e}")
        return False


def main():
    # Authenticate user first
    if not authenticate_user():
        print("[ERROR] Authentication failed. Exiting.")
        return

    while True:
        print("\n" + "=" * 50)
        print(f"[SEND] Sending messages as {current_username}")
        print("=" * 50)

        try:
            user_input_method = input(
                "\nChoose input method:\n1. Text Input\n2. Voice Input\n\nEnter choice (1 or 2): "
            ).strip()
            if user_input_method == "2":
                print("\n[VOICE] Listening for your message...")
                user_input = speech_recognition()
                if not user_input:
                    print("[ERROR] Could not recognize any speech. Try again.")
                    continue
                print(f"[VOICE INPUT] You said: {user_input}")
            else:
                user_input = input(
                    "\nEnter message command (or 'quit' to exit):\n> "
                ).strip()

            if user_input.lower() == "quit":
                print("[END] Goodbye!")
                logger.info(f"User {current_username} logged out")
                break

            if not user_input:
                continue

            print("\n[AI] Processing with AI...")
            extracted_data = extract_message_details(user_input)

            if not extracted_data:
                continue

            print(f"AI Response: {extracted_data}")

            # Parse the JSON response - clean markdown formatting
            try:
                cleaned_data = extracted_data.strip()
                if cleaned_data.startswith("```json"):
                    cleaned_data = (
                        cleaned_data.replace("```json", "").replace("```", "").strip()
                    )
                elif cleaned_data.startswith("```"):
                    cleaned_data = cleaned_data.replace("```", "").strip()

                data = json.loads(cleaned_data)
                recipient = data.get("recipient")
                message = data.get("message")

                if not recipient or not message:
                    print("[ERROR] Could not extract recipient and message")
                    logger.warning(
                        "Failed to extract recipient and message from AI response"
                    )
                    continue

                print(f"\n[SEND] Sending to {recipient}: {message}")
                send_message_to_server(recipient, message)

            except json.JSONDecodeError as e:
                print(f"[ERROR] Could not parse AI response: {e}")
                logger.error(f"JSON parsing error: {e}")
                print(f"Raw response: {extracted_data}")

        except KeyboardInterrupt:
            print("\n[END] Goodbye!")
            logger.info(f"User {current_username} exited")
            break
        except Exception as e:
            print(f"[ERROR] Error: {e}")
            logger.error(f"Unexpected error in main loop: {e}")
            continue


# if __name__ == "__main__":
#     main()

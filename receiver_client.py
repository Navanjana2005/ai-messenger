import os
import requests
import time
import logging
from mistralai import Mistral
import config
from text_to_speech import text_to_speech

# Configuration
MISTRAL_API_KEY = config.MISTRAL_API_KEY
SERVER_URL = "http://localhost:5000"
logger = logging.getLogger(__name__)

# Session variables
current_user_token = None
current_username = None


def authenticate_user():
    """Handle user signup/login"""
    global current_user_token, current_username

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
    global current_user_token, current_username

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
    global current_user_token, current_username

    print("\n[LOGIN] Login to Account")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    return login_with_credentials(username, password)


def login_with_credentials(username, password):
    """Authenticate with username and password"""
    global current_user_token, current_username

    try:
        payload = {"username": username, "password": password}

        response = requests.post(f"{SERVER_URL}/login", json=payload, timeout=10)

        if response.status_code == 200:
            data = response.json()
            current_user_token = data.get("token")
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


def format_message_with_ai(sender, message):
    """Use Mistral AI to format the received message naturally"""

    try:
        with Mistral(api_key=MISTRAL_API_KEY) as mistral:
            prompt = f"""
            Format this message naturally for spoken output:
            Sender: {sender}
            Message: {message}
            
            Create a natural spoken format like: "{sender} tells {message}"
            Respond ONLY with the formatted message, nothing else.
            """

            res = mistral.chat.complete(
                model="mistral-small-latest",
                messages=[{"content": prompt, "role": "user"}],
                stream=False,
            )

            formatted_message = res.choices[0].message.content
            return formatted_message
    except Exception as e:
        logger.error(f"AI formatting error: {e}")
        return None


def check_messages():
    """Check for new messages from the server"""
    try:
        response = requests.get(
            f"{SERVER_URL}/get_messages?token={current_user_token}", timeout=10
        )
        if response.status_code == 200:
            return response.json().get("messages", [])
        elif response.status_code == 401:
            print("[ERROR] Session expired. Please login again.")
            logger.warning("Session token expired")
            return None
        else:
            error_msg = response.json().get("error", "Error fetching messages")
            print(f"[ERROR] Error: {error_msg}")
            logger.warning(f"Failed to fetch messages: {error_msg}")
            return []
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        logger.error(f"Check messages error: {e}")
        return []


def mark_message_read(message_id):
    """Mark a message as read on the server"""
    try:
        payload = {"token": current_user_token}
        response = requests.post(
            f"{SERVER_URL}/mark_read/{message_id}", json=payload, timeout=10
        )
        if response.status_code != 200:
            logger.warning(f"Failed to mark message {message_id} as read")
    except Exception as e:
        logger.error(f"Error marking message as read: {e}")


def process_incoming_messages():
    """Process and display incoming messages"""
    messages = check_messages()

    if messages is None:
        return False  # Session expired

    if not messages:
        print("[NONE] No new messages")
        return True

    print(f"\n[NEW] You have {len(messages)} new message(s)!\n")

    for msg in messages:
        sender = msg["sender"]
        message = msg["message"]
        msg_id = msg["id"]
        timestamp = msg["timestamp"]

        print(f"[TIME] Received at: {timestamp}")
        print(f"[MSG] Raw message: {sender} -> {message}")

        # Format with AI
        print("[AI] Processing with AI...")
        formatted = format_message_with_ai(sender, message)

        if formatted:
            print(f"[TEXT] AI Output (Text): {formatted}")
            print(f"[TTS] Playing audio...")
            text_to_speech(formatted)
            logger.info(f"Message from {sender} processed and read aloud")
        else:
            print(f"[TEXT] Failed to format, raw message: {message}")

        print("-" * 50)

        # Mark as read
        mark_message_read(msg_id)

    return True


def main():
    global current_user_token, current_username

    # Authenticate user first
    if not authenticate_user():
        print("[ERROR] Authentication failed. Exiting.")
        return

    print("\n" + "=" * 50)
    print(f"[RECV] Receiving messages as {current_username}")
    print("=" * 50)
    print("\nChoose how to check messages:")
    print("1. Check once and exit")
    print("2. Check continuously (every 5 seconds)")
    print("3. Manual check (press Enter to check, 'quit' to exit)")

    mode = input("\nEnter choice (1/2/3): ").strip()

    try:
        if mode == "1":
            # Check once
            process_incoming_messages()

        elif mode == "2":
            # Check continuously
            print("Checking for messages every 5 seconds... (Press Ctrl+C to stop)")
            while True:
                success = process_incoming_messages()
                if not success:
                    print("[ERROR] Session expired. Please login again.")
                    break
                time.sleep(5)

        elif mode == "3":
            # Manual check
            print("Press Enter to check for messages, type 'quit' to exit")
            while True:
                user_input = input("\n> ").strip().lower()
                if user_input == "quit":
                    break
                success = process_incoming_messages()
                if not success:
                    print("[ERROR] Session expired. Please login again.")
                    break

        else:
            print("[ERROR] Invalid choice")

    except KeyboardInterrupt:
        print("\n[END] Goodbye!")
        logger.info(f"User {current_username} exited")


if __name__ == "__main__":
    main()
    main()

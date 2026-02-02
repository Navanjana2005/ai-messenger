#!/usr/bin/env python3
"""
AI Messenger - Main Entry Point
A voice-enabled messaging system powered by Mistral AI
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(log_dir, f"messenger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)





def check_dependencies():
    """Check if all required dependencies are installed"""
    missing_deps = []
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        from mistralai import Mistral
    except ImportError:
        missing_deps.append("mistralai")
    
    try:
        import config
        if not hasattr(config, 'MISTRAL_API_KEY'):
            print("[WARNING] MISTRAL_API_KEY not found in config.py")
            logger.warning("MISTRAL_API_KEY not configured")
    except ImportError:
        missing_deps.append("config.py (create this file with your MISTRAL_API_KEY)")
    
    if missing_deps:
        print("\n[ERROR] Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstall missing packages with:")
        print("  pip install requests mistralai")
        print("\nCreate config.py with:")
        print('  MISTRAL_API_KEY = "your-api-key-here"')
        return False
    
    return True


def check_server_connection():
    """Check if the server is accessible"""
    import requests
    
    server_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{server_url}/health", timeout=3)
        if response.status_code == 200:
            print(f"[OK] Server connection established at {server_url}")
            logger.info("Server connection successful")
            return True
    except requests.exceptions.ConnectionError:
        print(f"\n[WARNING] Cannot connect to server at {server_url}")
        print("Make sure the Flask server is running!")
        print("\nTo start the server, run:")
        print("  python server.py")
        logger.warning("Server connection failed")
        return False
    except Exception as e:
        print(f"[ERROR] Server check failed: {e}")
        logger.error(f"Server check error: {e}")
        return False


def display_menu():
    """Display main menu"""
    print("\n" + "=" * 55)
    print("                    MAIN MENU")
    print("=" * 55)
    print("\n  1. 📤 SEND Messages (Sender Client)")
    print("     - Send messages via text or voice input")
    print("     - AI-powered message extraction")
    print()
    print("  2. 📥 RECEIVE Messages (Receiver Client)")
    print("     - Check and receive messages")
    print("     - AI-formatted text-to-speech playback")
    print()
    print("  3. ℹ️  System Information")
    print()
    print("  4. ❌ Exit")
    print("\n" + "=" * 55)


def show_system_info():
    """Display system information"""
    print("\n" + "=" * 55)
    print("              SYSTEM INFORMATION")
    print("=" * 55)
    print(f"\n📋 Project: AI Messenger System")
    print(f"🤖 AI Model: Mistral AI (mistral-small-latest)")
    print(f"🌐 Server: http://localhost:5000")
    print(f"📁 Log File: {log_filename}")
    print()
    print("📦 Components:")
    print("  - sender_client.py: Message sending interface")
    print("  - receiver_client.py: Message receiving interface")
    print("  - Speech Recognition: Voice input support")
    print("  - Text-to-Speech: Audio message playback")
    print()
    print("🔑 Features:")
    print("  ✓ User authentication (signup/login)")
    print("  ✓ Voice and text input")
    print("  ✓ AI-powered message extraction")
    print("  ✓ Natural language formatting")
    print("  ✓ Text-to-speech output")
    print("  ✓ Session management")
    print("\n" + "=" * 55)
    input("\nPress Enter to continue...")


def run_sender_client():
    """Run the sender client"""
    try:
        import sender_client
        logger.info("Starting sender client")
        sender_client.main()
    except Exception as e:
        print(f"\n[ERROR] Failed to run sender client: {e}")
        logger.error(f"Sender client error: {e}")
        input("\nPress Enter to continue...")


def run_receiver_client():
    """Run the receiver client"""
    try:
        import receiver_client
        logger.info("Starting receiver client")
        receiver_client.main()
    except Exception as e:
        print(f"\n[ERROR] Failed to run receiver client: {e}")
        logger.error(f"Receiver client error: {e}")
        input("\nPress Enter to continue...")


def main():
    
    logger.info("=" * 50)
    logger.info("AI Messenger System Started")
    logger.info("=" * 50)
    
    # Check dependencies
    print("\n[INIT] Checking system dependencies...")
    if not check_dependencies():
        logger.error("Dependency check failed")
        return
    
    print("[OK] All dependencies satisfied")
    
    # Check server connection (non-blocking)
    print("\n[INIT] Checking server connection...")
    server_available = check_server_connection()
    
    if not server_available:
        choice = input("\nContinue anyway? (y/n): ").strip().lower()
        if choice != 'y':
            print("\n[EXIT] Please start the server and try again.")
            logger.info("User cancelled due to server unavailability")
            return
    
    # Main application loop
    while True:
        try:
            display_menu()
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == "1":
                logger.info("User selected: Sender Client")
                run_sender_client()
                
            elif choice == "2":
                logger.info("User selected: Receiver Client")
                run_receiver_client()
                
            elif choice == "3":
                logger.info("User selected: System Information")
                show_system_info()
                
            elif choice == "4":
                print("\n[EXIT] Thank you for using AI Messenger!")
                print("Goodbye! 👋\n")
                logger.info("Application closed by user")
                break
                
            else:
                print("\n[ERROR] Invalid choice. Please enter 1, 2, 3, or 4.")
                logger.warning(f"Invalid menu choice: {choice}")
                
        except KeyboardInterrupt:
            print("\n\n[EXIT] Application interrupted by user")
            logger.info("Application interrupted (Ctrl+C)")
            break
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}")
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            input("\nPress Enter to continue...")
    
    logger.info("AI Messenger System Shutdown")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        print(f"\n[CRITICAL ERROR] {e}")
        sys.exit(1)
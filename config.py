import os
import logging

# Mistral API Configuration
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    print("Getting ADMIN_MISTRAL_API_KEY from config.py")
    MISTRAL_API_KEY = "ENTER_YOUR_MISTRAL_API_KEY_HERE"

# Database Configuration
DATABASE = "ai_messenger.db"

# Security Configuration
PASSWORD_SALT_LENGTH = 32  # For password hashing
SESSION_TIMEOUT = 3600  # 1 hour in seconds

# Logging Configuration
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "ai_messenger.log")
LOG_LEVEL = logging.INFO

# Create logs directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging with UTF-8 encoding for Windows compatibility
import sys
import io

# Create file handler with UTF-8 encoding
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(LOG_LEVEL)

# Create console handler with UTF-8 encoding for Windows
if sys.platform == "win32":
    # For Windows, wrap stdout with UTF-8 encoding
    console_handler = logging.StreamHandler(
        io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    )
else:
    console_handler = logging.StreamHandler()

console_handler.setLevel(LOG_LEVEL)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

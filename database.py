import sqlite3
import hashlib
import secrets
from datetime import datetime
import logging
from config import DATABASE, logger


def get_db_connection():
    """Create database connection with row factory"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    """Hash password with salt using SHA-256"""
    salt = secrets.token_hex(32)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100000
    )
    return f"{salt}${password_hash.hex()}"


def verify_password(stored_hash, password):
    """Verify password against stored hash"""
    try:
        salt, hash_val = stored_hash.split("$")
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100000
        )
        return password_hash.hex() == hash_val
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def init_db():
    """Initialize database with required tables"""
    conn = get_db_connection()

    try:
        # Users table with authentication
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """
        )

        # Messages table with enhanced fields
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                read_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (recipient_id) REFERENCES users(id)
            )
        """
        )

        # Activity logs table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
        )

        # Sessions table for authentication tokens
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_valid BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
        )

        # Device tokens table for push notifications
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS device_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_token TEXT NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, device_token)
            )
        """
        )

        conn.commit()
        logger.info("[SUCCESS] Database initialized successfully!")
        print("[SUCCESS] Database initialized!")

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        print(f"[ERROR] Database initialization error: {e}")
    finally:
        conn.close()


def register_user(username, password, email=None):
    """Register a new user"""
    conn = get_db_connection()

    try:
        password_hash = hash_password(password)
        conn.execute(
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
            (username, password_hash, email),
        )
        conn.commit()
        logger.info(f"User registered successfully: {username}")
        return True, "User registered successfully"

    except sqlite3.IntegrityError as e:
        logger.warning(f"Registration failed - username already exists: {username}")
        return False, "Username already exists"
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False, str(e)
    finally:
        conn.close()


def login_user(username, password):
    """Authenticate user and create session"""
    conn = get_db_connection()

    try:
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ? AND is_active = 1",
            (username,),
        ).fetchone()

        if not user:
            logger.warning(f"Login failed - user not found: {username}")
            return False, "Invalid credentials", None

        if not verify_password(user["password_hash"], password):
            logger.warning(f"Login failed - incorrect password: {username}")
            return False, "Invalid credentials", None

        # Update last login
        conn.execute(
            "UPDATE users SET last_login = ? WHERE id = ?", (datetime.now(), user["id"])
        )

        # Create session token
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (user_id, token) VALUES (?, ?)", (user["id"], token)
        )
        conn.commit()

        logger.info(f"User logged in successfully: {username}")
        return True, "Login successful", token

    except Exception as e:
        logger.error(f"Login error: {e}")
        return False, str(e), None
    finally:
        conn.close()


def verify_session_token(token):
    """Verify if session token is valid"""
    conn = get_db_connection()

    try:
        session = conn.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND is_valid = 1", (token,)
        ).fetchone()

        if session:
            user = conn.execute(
                "SELECT id, username FROM users WHERE id = ?", (session["user_id"],)
            ).fetchone()
            return True, user

        return False, None

    except Exception as e:
        logger.error(f"Session verification error: {e}")
        return False, None
    finally:
        conn.close()


def log_activity(user_id, action, details=None, ip_address=None, status="success"):
    """Log user activity"""
    conn = get_db_connection()

    try:
        conn.execute(
            "INSERT INTO activity_logs (user_id, action, details, ip_address, status) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, details, ip_address, status),
        )
        conn.commit()
        logger.info(
            f"Activity logged - User: {user_id}, Action: {action}, Status: {status}"
        )

    except Exception as e:
        logger.error(f"Activity logging error: {e}")
    finally:
        conn.close()


def get_user_by_username(username):
    """Get user by username"""
    conn = get_db_connection()

    try:
        user = conn.execute(
            "SELECT id, username, email, created_at, last_login FROM users WHERE username = ?", (username,)
        ).fetchone()
        return user

    except Exception as e:
        logger.error(f"Get user error: {e}")
        return None
    finally:
        conn.close()

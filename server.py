from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import logging
from config import logger, DATABASE
from database import (
    init_db,
    register_user,
    login_user,
    verify_session_token,
    log_activity,
    get_user_by_username,
    get_db_connection,
)

app = Flask(__name__)


def get_client_ip():
    """Get client IP address from request"""
    return request.environ.get("REMOTE_ADDR", "Unknown")


# ==================== Authentication Endpoints ====================


@app.route("/signup", methods=["POST"])
def signup():
    """Register a new user"""
    try:
        data = request.json or {}
        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()
        email = (data.get("email") or "").strip() or None

        # Validation
        if not username or not password:
            logger.warning(f"Signup attempt with missing fields from {get_client_ip()}")
            return jsonify({"error": "Username and password required"}), 400

        if len(password) < 6:
            logger.warning(f"Signup attempt with weak password from {get_client_ip()}")
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        if len(username) < 3:
            logger.warning(f"Signup attempt with short username from {get_client_ip()}")
            return jsonify({"error": "Username must be at least 3 characters"}), 400

        # Register user
        success, message = register_user(username, password, email)

        if success:
            logger.info(f"New user registered: {username} from {get_client_ip()}")
            log_activity(None, "user_signup", f"Username: {username}", get_client_ip())
            return jsonify({"status": "success", "message": message}), 201
        else:
            logger.warning(f"Signup failed for {username}: {message}")
            return jsonify({"error": message}), 400

    except Exception as e:
        logger.error(f"Signup endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/login", methods=["POST"])
def login():
    """Authenticate user and create session"""
    try:
        data = request.json or {}
        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()

        if not username or not password:
            logger.warning(f"Login attempt with missing fields from {get_client_ip()}")
            return jsonify({"error": "Username and password required"}), 400

        # Login user
        success, message, token = login_user(username, password)

        if success:
            user = get_user_by_username(username)
            logger.info(f"User logged in: {username} from {get_client_ip()}")
            log_activity(user["id"], "user_login", None, get_client_ip())
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": message,
                        "token": token,
                        "user_id": user["id"],
                        "username": username,
                    }
                ),
                200,
            )
        else:
            logger.warning(f"Login failed for {username} from {get_client_ip()}")
            log_activity(
                None,
                "failed_login_attempt",
                f"Username: {username}",
                get_client_ip(),
                "failed",
            )
            return jsonify({"error": message}), 401

    except Exception as e:
        logger.error(f"Login endpoint error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ==================== Message Endpoints ====================


@app.route("/send_message", methods=["POST"])
def send_message():
    """Send message between authenticated users"""
    try:
        data = request.json or {}
        token = data.get("token")
        recipient = (data.get("recipient") or "").strip()
        message = (data.get("message") or "").strip()

        # Verify token
        valid, user = verify_session_token(token)
        if not valid:
            logger.warning(
                f"Send message attempt with invalid token from {get_client_ip()}"
            )
            return jsonify({"error": "Unauthorized - Invalid or expired token"}), 401

        if not recipient or not message:
            logger.warning(
                f"Send message with missing fields from user {user['username']}"
            )
            return jsonify({"error": "Recipient and message required"}), 400

        # Get recipient user
        recipient_user = get_user_by_username(recipient)
        if not recipient_user:
            logger.warning(
                f"Send message to non-existent user: {recipient} from {user['username']}"
            )
            return jsonify({"error": "Recipient user not found"}), 404

        # Store message
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO messages (sender_id, recipient_id, message) VALUES (?, ?, ?)",
            (user["id"], recipient_user["id"], message),
        )
        conn.commit()
        conn.close()

        logger.info(f"Message sent from {user['username']} to {recipient}")
        log_activity(user["id"], "send_message", f"To: {recipient}", get_client_ip())

        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Message sent from {user['username']} to {recipient}",
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Send message error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_messages", methods=["GET"])
def get_messages():
    """Retrieve unread messages for authenticated user"""
    try:
        token = request.args.get("token")

        # Verify token
        valid, user = verify_session_token(token)
        if not valid:
            logger.warning(
                f"Get messages attempt with invalid token from {get_client_ip()}"
            )
            return jsonify({"error": "Unauthorized - Invalid or expired token"}), 401

        conn = get_db_connection()
        messages = conn.execute(
            """SELECT m.id, u.username as sender, m.message, m.created_at 
               FROM messages m
               JOIN users u ON m.sender_id = u.id
               WHERE m.recipient_id = ? AND m.is_read = 0
               ORDER BY m.created_at DESC""",
            (user["id"],),
        ).fetchall()

        message_list = []
        for msg in messages:
            message_list.append(
                {
                    "id": msg["id"],
                    "sender": msg["sender"],
                    "message": msg["message"],
                    "timestamp": msg["created_at"],
                }
            )

        conn.close()

        logger.info(
            f"Retrieved {len(message_list)} messages for user {user['username']}"
        )
        log_activity(
            user["id"],
            "get_messages",
            f"Retrieved {len(message_list)} messages",
            get_client_ip(),
        )

        return jsonify({"messages": message_list}), 200

    except Exception as e:
        logger.error(f"Get messages error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/mark_read/<int:message_id>", methods=["POST"])
def mark_read(message_id):
    """Mark a message as read"""
    try:
        data = request.json
        token = data.get("token")

        # Verify token
        valid, user = verify_session_token(token)
        if not valid:
            logger.warning(
                f"Mark read attempt with invalid token from {get_client_ip()}"
            )
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        conn.execute(
            "UPDATE messages SET is_read = 1, read_at = ? WHERE id = ? AND recipient_id = ?",
            (datetime.now(), message_id, user["id"]),
        )
        conn.commit()
        conn.close()

        logger.info(f"Message {message_id} marked as read by user {user['username']}")
        log_activity(
            user["id"],
            "mark_message_read",
            f"Message ID: {message_id}",
            get_client_ip(),
        )

        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Mark read error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_conversation/<recipient_username>", methods=["GET"])
def get_conversation(recipient_username):
    """Get conversation history between two users"""
    try:
        token = request.args.get("token")

        # Verify token
        valid, user = verify_session_token(token)
        if not valid:
            logger.warning(
                f"Get conversation with invalid token from {get_client_ip()}"
            )
            return jsonify({"error": "Unauthorized"}), 401

        recipient_user = get_user_by_username(recipient_username)
        if not recipient_user:
            logger.warning(
                f"Conversation requested with non-existent user: {recipient_username}"
            )
            return jsonify({"error": "User not found"}), 404

        conn = get_db_connection()
        messages = conn.execute(
            """SELECT m.id, u.username as sender, m.message, m.is_read, m.created_at 
               FROM messages m
               JOIN users u ON m.sender_id = u.id
               WHERE (m.sender_id = ? AND m.recipient_id = ?) 
                  OR (m.sender_id = ? AND m.recipient_id = ?)
               ORDER BY m.created_at ASC""",
            (user["id"], recipient_user["id"], recipient_user["id"], user["id"]),
        ).fetchall()

        message_list = []
        for msg in messages:
            message_list.append(
                {
                    "id": msg["id"],
                    "sender": msg["sender"],
                    "message": msg["message"],
                    "is_read": msg["is_read"],
                    "timestamp": msg["created_at"],
                }
            )

        conn.close()

        logger.info(
            f"Retrieved conversation between {user['username']} and {recipient_username}"
        )
        log_activity(
            user["id"],
            "view_conversation",
            f"With: {recipient_username}",
            get_client_ip(),
        )

        return jsonify({"conversation": message_list}), 200

    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== Mobile App Endpoints ====================


@app.route("/get_all_users", methods=["GET"])
def get_all_users():
    """Get list of all users (for contact list)"""
    try:
        token = request.args.get("token")

        # Verify token
        valid, user = verify_session_token(token)
        if not valid:
            logger.warning(
                f"Get users attempt with invalid token from {get_client_ip()}"
            )
            return jsonify({"error": "Unauthorized"}), 401

        conn = get_db_connection()
        users = conn.execute(
            """SELECT id, username, email, created_at FROM users 
               WHERE is_active = 1 AND id != ?
               ORDER BY username ASC""",
            (user["id"],),
        ).fetchall()

        user_list = []
        for u in users:
            user_list.append(
                {
                    "id": u["id"],
                    "username": u["username"],
                    "email": u["email"],
                    "joined_at": u["created_at"],
                }
            )

        conn.close()

        logger.info(f"User {user['username']} retrieved contacts list")
        return jsonify({"users": user_list}), 200

    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_user_profile", methods=["GET"])
def get_user_profile():
    """Get current user profile"""
    try:
        token = request.args.get("token")

        # Verify token
        valid, user = verify_session_token(token)
        if not valid:
            return jsonify({"error": "Unauthorized"}), 401

        return (
            jsonify(
                {
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "email": user["email"],
                        "created_at": user["created_at"],
                        "last_login": user["last_login"],
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/register_device", methods=["POST"])
def register_device():
    """Register device for push notifications"""
    try:
        data = request.json or {}
        token = data.get("token")
        device_token = data.get("device_token")

        # Verify token
        valid, user = verify_session_token(token)
        if not valid:
            return jsonify({"error": "Unauthorized"}), 401

        if not device_token:
            return jsonify({"error": "Device token required"}), 400

        # Store device token (in production, use proper push notification service)
        conn = get_db_connection()
        conn.execute(
            """INSERT OR REPLACE INTO device_tokens (user_id, device_token, registered_at)
               VALUES (?, ?, ?)""",
            (user["id"], device_token, datetime.now()),
        )
        conn.commit()
        conn.close()

        logger.info(f"Device registered for user {user['username']}")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Register device error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_conversation_v2/<recipient_username>", methods=["GET"])
def get_conversation_v2(recipient_username):
    """Get full conversation history with pagination (for mobile app)"""
    try:
        token = request.args.get("token")
        limit = request.args.get("limit", default=50, type=int)
        offset = request.args.get("offset", default=0, type=int)

        # Verify token
        valid, user = verify_session_token(token)
        if not valid:
            return jsonify({"error": "Unauthorized"}), 401

        recipient_user = get_user_by_username(recipient_username)
        if not recipient_user:
            return jsonify({"error": "User not found"}), 404

        conn = get_db_connection()
        
        # Get total count
        count = conn.execute(
            """SELECT COUNT(*) as total FROM messages m
               WHERE (m.sender_id = ? AND m.recipient_id = ?) 
                  OR (m.sender_id = ? AND m.recipient_id = ?)""",
            (user["id"], recipient_user["id"], recipient_user["id"], user["id"]),
        ).fetchone()["total"]

        # Get paginated messages
        messages = conn.execute(
            """SELECT m.id, u.username as sender, m.message, m.is_read, m.created_at 
               FROM messages m
               JOIN users u ON m.sender_id = u.id
               WHERE (m.sender_id = ? AND m.recipient_id = ?) 
                  OR (m.sender_id = ? AND m.recipient_id = ?)
               ORDER BY m.created_at DESC
               LIMIT ? OFFSET ?""",
            (user["id"], recipient_user["id"], recipient_user["id"], user["id"], limit, offset),
        ).fetchall()

        message_list = []
        for msg in messages:
            message_list.append(
                {
                    "id": msg["id"],
                    "sender": msg["sender"],
                    "is_own_message": msg["sender"] == user["username"],
                    "message": msg["message"],
                    "is_read": msg["is_read"],
                    "timestamp": msg["created_at"],
                }
            )

        conn.close()

        return (
            jsonify(
                {
                    "conversation": message_list[::-1],  # Reverse to show oldest first
                    "total_messages": count,
                    "has_more": offset + limit < count,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Get conversation v2 error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    init_db()
    logger.info("[START] AI Messenger Server starting...")
    app.run(debug=True, host="0.0.0.0", port=5000)

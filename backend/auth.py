# ─────────────────────────────────────────────────────
# auth.py — handles user registration and login
# Passwords are hashed using bcrypt
# A hash is a one-way scramble — cannot be reversed
# ─────────────────────────────────────────────────────

import sqlite3
import bcrypt          # for hashing passwords securely
from typing import Optional
from backend.database import get_connection, create_tables


def register_user(username: str, password: str) -> bool:
    """
    Creates a new user account.
    Returns True if successful.
    Returns False if username is already taken.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # Hash the password before saving
    # encode("utf-8") converts string to bytes — bcrypt needs bytes
    # gensalt() generates a random salt — makes every hash unique
    # even if two users have the same password, their hashes differ
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        """, (username, password_hash))
        conn.commit()
        return True   # registration successful

    except sqlite3.IntegrityError:
        # IntegrityError happens when UNIQUE constraint fails
        # meaning username already exists in the database
        return False

    finally:
        # finally always runs — even if an error occurred
        # ensures connection is always closed
        conn.close()


def login_user(username: str, password: str) -> Optional[int]:
    """
    Checks login credentials.
    Returns user_id if correct.
    Returns None if username not found or password is wrong.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # Find the user by username
    cursor.execute("""
        SELECT id, password_hash
        FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()   # returns one row or None
    conn.close()

    # Username not found in database
    if user is None:
        return None

    # checkpw hashes the entered password and compares to stored hash
    # returns True if they match, False if not
    password_matches = bcrypt.checkpw(
        password.encode("utf-8"),
        user["password_hash"]
    )

    if password_matches:
        return user["id"]   # login success — return user_id
    return None             # wrong password


def get_user_by_id(user_id: int) -> Optional[dict]:
    """
    Gets user details by their ID.
    Used to show the logged in username in the sidebar.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username FROM users WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)
    return None


def ensure_guest_user() -> int:
    """
    Ensures a default guest user exists.
    Returns the guest user's ID.
    """
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", ("guest",))
    row = cursor.fetchone()

    if row is not None:
        guest_id = row["id"]
    else:
        password_hash = bcrypt.hashpw(
            "guest_default_password".encode("utf-8"),
            bcrypt.gensalt()
        )
        cursor.execute("""
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
        """, ("guest", password_hash))
        conn.commit()
        guest_id = cursor.lastrowid

    conn.close()
    return guest_id

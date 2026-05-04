# ─────────────────────────────────────────────────────
# database.py — saves and retrieves routes
# Uses SQLite — a simple file-based database
# No server needed, database is just one .db file
# ─────────────────────────────────────────────────────

import sqlite3      # built into Python — no install needed
import os           # for creating folders
from datetime import datetime   # for timestamps
from typing import List, Dict   # type hints

# Path to the database file
# All data is stored in this single file
DB_PATH = "data/traffic_routes.db"


def get_connection():
    """
    Opens a connection to the database.
    Creates the data/ folder if it does not exist yet.
    row_factory lets us access columns by name instead of index.
    e.g. row['username'] instead of row[0]
    """
    os.makedirs("data", exist_ok=True)   # exist_ok=True means don't crash if folder exists
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row       # allows row['column_name'] access
    return conn


def create_tables():
    """
    Creates all database tables if they don't exist yet.
    IF NOT EXISTS means this is safe to call multiple times.
    """
    conn   = get_connection()
    cursor = conn.cursor()   # cursor is used to run SQL commands

    # users table — stores login information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    # INTEGER PRIMARY KEY AUTOINCREMENT → id goes 1, 2, 3... automatically
    # TEXT UNIQUE → no two users can have the same username
    # NOT NULL → this field cannot be empty

    # routes table — stores every route a user searches
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            origin      TEXT NOT NULL,
            destination TEXT NOT NULL,
            distance    TEXT,
            duration    TEXT,
            timestamp   TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    # FOREIGN KEY → links user_id here to the id in the users table
    # This means every route belongs to a specific user

    # frequent_routes table — tracks how often each route is used
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frequent_routes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            origin      TEXT NOT NULL,
            destination TEXT NOT NULL,
            trip_count  INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    # DEFAULT 1 → trip_count starts at 1 when first inserted

    conn.commit()   # commit = save all changes to the file
    conn.close()    # always close when done


def save_route(user_id: int, origin: str,
               destination: str, distance: str, duration: str):
    """
    Saves a searched route to history.
    Also updates frequent_routes — increments count if route exists,
    inserts new row if it's the first time.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # Save to route history — always adds a new row
    cursor.execute("""
        INSERT INTO routes (user_id, origin, destination, distance, duration, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, origin, destination, distance, duration,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    # ? = placeholder — Python fills these in safely
    # This prevents SQL injection attacks

    # Check if this exact route already exists in frequent_routes
    cursor.execute("""
        SELECT id FROM frequent_routes
        WHERE user_id=? AND origin=? AND destination=?
    """, (user_id, origin, destination))

    existing = cursor.fetchone()   # returns one row or None

    if existing:
        # Route already exists → just increment the count by 1
        cursor.execute("""
            UPDATE frequent_routes
            SET trip_count = trip_count + 1
            WHERE id = ?
        """, (existing["id"],))
    else:
        # First time this route is searched → insert it fresh
        cursor.execute("""
            INSERT INTO frequent_routes (user_id, origin, destination, trip_count)
            VALUES (?, ?, ?, 1)
        """, (user_id, origin, destination))

    conn.commit()
    conn.close()


def get_route_history(user_id: int) -> List[Dict]:
    """
    Returns all routes a user has ever searched.
    Newest first — ORDER BY timestamp DESC.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT origin, destination, distance, duration, timestamp
        FROM routes
        WHERE user_id = ?
        ORDER BY timestamp DESC
    """, (user_id,))

    rows = cursor.fetchall()   # returns all matching rows as a list
    conn.close()

    # dict(row) converts each Row object to a plain dictionary
    # so it can be used with pandas DataFrame easily
    return [dict(row) for row in rows]


def get_frequent_routes(user_id: int) -> List[Dict]:
    """
    Returns unique routes sorted by how often they are used.
    Most used route appears first.
    """
    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT origin, destination, trip_count
        FROM frequent_routes
        WHERE user_id = ?
        ORDER BY trip_count DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
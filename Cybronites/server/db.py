import sqlite3
import os
from typing import Optional

# SECURE FEDERATED LEARNING | DB CONFIGURATION
# Using environment variables for runtime flexibility
class Settings:
    def __init__(self):
        self.DB_PATH = os.environ.get("GUARDIAN_DB_PATH", "Cybronites/guardian.db")
        self.JWT_SECRET = os.environ.get("JWT_SECRET", "supersecret-key-1234")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("TOKEN_EXPIRE", 1440))
        
        # Email (Optional)
        self.MAIL_FROM = os.environ.get("MAIL_FROM", "verified@guardian.sys")

settings = Settings()

# SQLite Connection Manager
def get_db():
    """Returns a connection to the SQLite database."""
    # Ensure the path is absolute relative to project root if needed
    db_path = settings.DB_PATH
    if not os.path.isabs(db_path):
        # Assuming project root context
        db_path = os.path.join(os.getcwd(), db_path)
    
    # Handle the case where we are in different subdirectories
    if not os.path.exists(db_path):
        # Fallback to local directory if relative path fails
        alt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "guardian.db")
        if os.path.exists(alt_path):
            db_path = alt_path
        
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Helper to initialize tables
def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_verified BOOLEAN DEFAULT 0,
                role TEXT DEFAULT 'Researcher',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create nodes table for telemetry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                name TEXT,
                last_seen TIMESTAMP,
                trust_score REAL,
                ip_address TEXT
            )
        """)

        # Create shards table for registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shards (
                id TEXT PRIMARY KEY,
                name TEXT,
                region TEXT,
                load REAL,
                status TEXT,
                encryption TEXT
            )
        """)
        
        # Seed default shards if empty
        cursor.execute("SELECT COUNT(*) FROM shards")
        if cursor.fetchone()[0] == 0:
            shards = [
                ('SHARD-001', 'Institutional_Core', 'US-East', 0.45, 'ACTIVE', 'AES-256'),
                ('SHARD-002', 'Federated_Relay', 'EU-West', 0.12, 'ACTIVE', 'AES-256'),
                ('SHARD-003', 'Audit_Vault', 'Global', 0.89, 'FULL', 'AES-256')
            ]
            cursor.executemany("INSERT INTO shards (id, name, region, load, status, encryption) VALUES (?, ?, ?, ?, ?, ?)", shards)
            print("  [DB_INIT] Default institutional shards seeded.")
        
        # Seed default admin if table is empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            admin_id = "admin-001"
            # Hash for 'password123' generated with bcrypt
            admin_pwd_hash = "$2b$12$No.gYWLEIuKbrlPE/XJAVuF5dI9wdETB/DZq.nYAqTfEQws4xJK7G" 
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, is_verified, role)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (admin_id, "ADMIN", "research@institution.sys", admin_pwd_hash, 1, "Administrator"))
            print("  [DB_INIT] Default academic administrator created (ADMIN/password123)")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  [DB_INIT_ERROR] {e}")

# Initialize on import
init_db()

import sqlite3
import os
from datetime import datetime

class DBManager:
    """
    Database Manager for the Postman Collection -> Pytest Migrator.
    Handles connections and CRUD operations for SQLite.
    """

    def __init__(self, db_path=None):
        if db_path is None:
            # Fallback to default path relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.db_path = os.getenv("DATABASE_PATH", os.path.join(base_dir, "database", "pytest_migrator.db"))
        else:
            self.db_path = db_path

        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self.init_db()

    def get_connection(self):
        """Returns a sqlite3 connection with Row factory configured."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Initializes database schema if tables do not exist."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS uploaded_collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_name TEXT NOT NULL,
                file_name TEXT NOT NULL,
                uploaded_by TEXT NOT NULL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_apis INTEGER NOT NULL,
                status TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS api_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_id INTEGER NOT NULL,
                api_name TEXT,
                method TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                headers TEXT,
                request_body TEXT,
                query_params TEXT,
                FOREIGN KEY (collection_id) REFERENCES uploaded_collections(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS generated_testcases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_id INTEGER NOT NULL,
                testcase_name TEXT NOT NULL,
                testcase_type TEXT NOT NULL,
                expected_result TEXT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (api_id) REFERENCES api_details(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS generated_scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_id INTEGER NOT NULL,
                script_name TEXT NOT NULL,
                script_content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (api_id) REFERENCES api_details(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS ai_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_id INTEGER NOT NULL,
                recommendation TEXT NOT NULL,
                recommendation_type TEXT NOT NULL,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (api_id) REFERENCES api_details(id) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                onboarding_completed INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for query in queries:
                cursor.execute(query)
            conn.commit()

        # Dynamic schema adjustment migration for onboarding_completed
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT onboarding_completed FROM users LIMIT 1;")
        except sqlite3.OperationalError:
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("ALTER TABLE users ADD COLUMN onboarding_completed INTEGER DEFAULT 0;")
                    conn.commit()
            except Exception:
                pass

    # --- UPLOADED COLLECTIONS CRUD ---

    def insert_collection(self, collection_name, file_name, uploaded_by, total_apis, status="Pending"):
        """Inserts a new collection upload and returns its ID."""
        sql = """
        INSERT INTO uploaded_collections (collection_name, file_name, uploaded_by, total_apis, status)
        VALUES (?, ?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (collection_name, file_name, uploaded_by, total_apis, status))
            conn.commit()
            return cursor.lastrowid

    def update_collection_status(self, collection_id, status):
        """Updates the processing status of a collection."""
        sql = "UPDATE uploaded_collections SET status = ? WHERE id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (status, collection_id))
            conn.commit()

    def get_collection(self, collection_id):
        """Fetches details of a specific collection."""
        sql = "SELECT * FROM uploaded_collections WHERE id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (collection_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_collection(self, collection_id):
        """Deletes a collection and cascades to its API details and test artifacts."""
        sql = "DELETE FROM uploaded_collections WHERE id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (collection_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_collections(self):
        """Fetches all uploaded collections."""
        sql = "SELECT * FROM uploaded_collections ORDER BY uploaded_at DESC;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]

    # --- API DETAILS CRUD ---

    def insert_api_details(self, collection_id, api_name, method, endpoint, headers=None, request_body=None, query_params=None):
        """Inserts extracted API endpoint details and returns its ID."""
        sql = """
        INSERT INTO api_details (collection_id, api_name, method, endpoint, headers, request_body, query_params)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (collection_id, api_name, method, endpoint, headers, request_body, query_params))
            conn.commit()
            return cursor.lastrowid

    def get_apis_for_collection(self, collection_id):
        """Fetches all APIs associated with a collection."""
        sql = "SELECT * FROM api_details WHERE collection_id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (collection_id,))
            return [dict(row) for row in cursor.fetchall()]

    # --- GENERATED TESTCASES CRUD ---

    def insert_testcase(self, api_id, testcase_name, testcase_type, expected_result):
        """Inserts a generated test case."""
        sql = """
        INSERT INTO generated_testcases (api_id, testcase_name, testcase_type, expected_result)
        VALUES (?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (api_id, testcase_name, testcase_type, expected_result))
            conn.commit()
            return cursor.lastrowid

    def get_testcases_for_api(self, api_id):
        """Fetches all test cases for a specific API."""
        sql = "SELECT * FROM generated_testcases WHERE api_id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (api_id,))
            return [dict(row) for row in cursor.fetchall()]

    # --- GENERATED SCRIPTS CRUD ---

    def insert_script(self, api_id, script_name, script_content):
        """Inserts generated pytest script details."""
        sql = """
        INSERT INTO generated_scripts (api_id, script_name, script_content)
        VALUES (?, ?, ?);
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (api_id, script_name, script_content))
            conn.commit()
            return cursor.lastrowid

    def get_script_for_api(self, api_id):
        """Fetches generated scripts for a specific API."""
        sql = "SELECT * FROM generated_scripts WHERE api_id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (api_id,))
            return [dict(row) for row in cursor.fetchall()]

    # --- AI RECOMMENDATIONS CRUD ---

    def insert_recommendation(self, api_id, recommendation, recommendation_type):
        """Inserts an AI recommendation."""
        sql = """
        INSERT INTO ai_recommendations (api_id, recommendation, recommendation_type)
        VALUES (?, ?, ?);
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (api_id, recommendation, recommendation_type))
            conn.commit()
            return cursor.lastrowid

    def get_recommendations_for_api(self, api_id):
        """Fetches AI recommendations for a specific API."""
        sql = "SELECT * FROM ai_recommendations WHERE api_id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (api_id,))
            return [dict(row) for row in cursor.fetchall()]

    # --- USER AUTH LOGISTICS ---

    def insert_user(self, full_name, email, password_hash):
        """Creates a new user account profile in safety."""
        sql = """
        INSERT INTO users (full_name, email, password_hash)
        VALUES (?, ?, ?);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (full_name, email, password_hash))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Email address violation constraint
            return None

    def get_user_by_email(self, email):
        """Looks up a user profile by their email handle."""
        sql = "SELECT * FROM users WHERE email = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id):
        """Looks up a user profile by their user ID."""
        sql = "SELECT * FROM users WHERE id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_user_onboarding_completed(self, user_id, completed=1):
        """Updates the onboarding completion flag for a user."""
        sql = "UPDATE users SET onboarding_completed = ? WHERE id = ?;"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (completed, user_id))
            conn.commit()


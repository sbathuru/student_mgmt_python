import os
import threading
from typing import Optional, List

try:
    import oracledb
except ImportError:  # pragma: no cover - optional dependency
    oracledb = None


class OracleUserRecord:
    def __init__(self, user_id: int, email: str, password_hash: str):
        self.id = user_id
        self.email = email
        self.password_hash = password_hash


class OracleUserStore:
    def __init__(self):
        if oracledb is None:
            raise RuntimeError("Oracle user store requires the 'oracledb' package")
        self._user = os.getenv("ORACLE_USER")
        self._password = os.getenv("ORACLE_PASSWORD")
        self._dsn = os.getenv("ORACLE_DSN")
        if not self._user or not self._password or not self._dsn:
            raise ValueError("Oracle configuration is required for OracleUserStore")
        self._lock = threading.Lock()
        self._ensure_schema()

    def _connect(self):
        return oracledb.connect(user=self._user, password=self._password, dsn=self._dsn)

    def _ensure_schema(self):
        conn = self._connect()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    BEGIN
                      EXECUTE IMMEDIATE 'CREATE TABLE users (
                        id NUMBER PRIMARY KEY,
                        email VARCHAR2(255) NOT NULL UNIQUE,
                        password_hash VARCHAR2(512) NOT NULL
                      )';
                    EXCEPTION
                      WHEN OTHERS THEN
                        IF SQLCODE != -955 THEN
                          RAISE;
                        END IF;
                    END;
                    """
                )
                cursor.execute(
                    """
                    BEGIN
                      EXECUTE IMMEDIATE 'CREATE SEQUENCE users_seq START WITH 1 INCREMENT BY 1';
                    EXCEPTION
                      WHEN OTHERS THEN
                        IF SQLCODE != -955 THEN
                          RAISE;
                        END IF;
                    END;
                    """
                )
        finally:
            conn.close()

    def add_user(self, email: str, password_hash: str) -> OracleUserRecord:
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT users_seq.NEXTVAL FROM dual")
                    user_id = cursor.fetchone()[0]
                    try:
                        cursor.execute(
                            "INSERT INTO users (id, email, password_hash) VALUES (:1, :2, :3)",
                            (user_id, email.lower(), password_hash),
                        )
                    except oracledb.IntegrityError:
                        raise ValueError("User already exists")
            finally:
                conn.close()
            return OracleUserRecord(user_id, email, password_hash)

    def find_by_email(self, email: str) -> Optional[OracleUserRecord]:
        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, password_hash FROM users WHERE LOWER(email)=LOWER(:1)", (email,))
                row = cursor.fetchone()
            finally:
                conn.close()
            if row:
                return OracleUserRecord(row[0], row[1], row[2])
            return None

    def get_by_id(self, user_id: int) -> Optional[OracleUserRecord]:
        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, password_hash FROM users WHERE id = :1", (user_id,))
                row = cursor.fetchone()
            finally:
                conn.close()
            if row:
                return OracleUserRecord(row[0], row[1], row[2])
            return None

    def list_users(self) -> List[OracleUserRecord]:
        with self._lock:
            conn = self._connect()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, password_hash FROM users ORDER BY id")
                rows = cursor.fetchall()
            finally:
                conn.close()
            return [OracleUserRecord(r[0], r[1], r[2]) for r in rows]

    def update_password(self, user_id: int, password_hash: str) -> Optional[OracleUserRecord]:
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET password_hash = :1 WHERE id = :2", (password_hash, user_id))
            finally:
                conn.close()
            return self.get_by_id(user_id)

    def delete_user(self, user_id: int) -> bool:
        with self._lock:
            conn = self._connect()
            try:
                with conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM users WHERE id = :1", (user_id,))
                    deleted = cursor.rowcount > 0
            finally:
                conn.close()
            return deleted

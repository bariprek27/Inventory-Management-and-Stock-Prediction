"""
database/connection.py
Manages MySQL connection pool for StockWise.
"""
import mysql.connector
from mysql.connector import pooling, Error
import os

# ─── DB CONFIG ────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("SW_DB_HOST",   "localhost"),
    "port":     int(os.environ.get("SW_DB_PORT", 3306)),
    "user":     os.environ.get("SW_DB_USER",   "root"),
    "password": os.environ.get("SW_DB_PASS",   "root123"),
    "database": os.environ.get("SW_DB_NAME",   "stockwise"),
    "charset":  "utf8mb4",
    "autocommit": False,
    "connection_timeout": 10,
}

_pool: pooling.MySQLConnectionPool | None = None


def init_pool(pool_size: int = 5) -> None:
    """Create the connection pool. Call once at startup."""
    global _pool
    try:
        _pool = pooling.MySQLConnectionPool(
            pool_name="stockwise_pool",
            pool_size=pool_size,
            **DB_CONFIG,
        )
    except Error as e:
        raise RuntimeError(f"Cannot create DB pool: {e}") from e


def get_connection() -> mysql.connector.MySQLConnection:
    """Return a connection from the pool (caller must close it)."""
    global _pool
    if _pool is None:
        init_pool()
    try:
        return _pool.get_connection()
    except Error as e:
        raise RuntimeError(f"Cannot get DB connection: {e}") from e


def test_connection() -> bool:
    """Quick ping to verify DB is reachable."""
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception:
        return False

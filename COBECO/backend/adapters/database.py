from contextlib import contextmanager
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor

from backend.config import Settings


class Database:
    def __init__(self, settings: Settings):
        self.settings = settings

    def connect(self):
        s = self.settings
        return pymysql.connect(
            host=s.mysql_host,
            port=s.mysql_port,
            user=s.mysql_user,
            password=s.mysql_password,
            database=s.mysql_database,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
            connect_timeout=5,
            read_timeout=10,
            write_timeout=10,
            init_command="SET time_zone = '+00:00'",
        )

    @contextmanager
    def transaction(self):
        connection = self.connect()
        try:
            connection.begin()
            with connection.cursor() as cursor:
                yield cursor
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def health(self):
        with self.transaction() as cursor:
            cursor.execute("SELECT 1")

    def migrate(self):
        # MySQL DDL commits implicitly. Each migration is restartable; record only after all statements.
        with self.connect() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT GET_LOCK('cobeco_migrations', 30) AS acquired")
            if cursor.fetchone()["acquired"] != 1:
                raise RuntimeError("Não foi possível obter lock de migrations")
            try:
                cursor.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(100) PRIMARY KEY,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB""")
                for path in sorted((Path(__file__).parents[1] / "migrations").glob("*.sql")):
                    cursor.execute("SELECT version FROM schema_migrations WHERE version=%s", (path.name,))
                    if cursor.fetchone():
                        continue
                    for statement in path.read_text(encoding="utf-8").split(";"):
                        if statement.strip():
                            cursor.execute(statement)
                    cursor.execute("INSERT INTO schema_migrations(version) VALUES (%s)", (path.name,))
                    connection.commit()
            finally:
                cursor.execute("SELECT RELEASE_LOCK('cobeco_migrations')")

from sqlalchemy import create_engine, Column, String, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
from sqlalchemy import text

# Создаем базу данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./controller.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    totp_secret = Column(LargeBinary, nullable=True)  # Зашифрованный секрет (AES-GCM), хранится как bytes
    secret_expires_at = Column(DateTime, nullable=True)  # Дата истечения секрета
    created_at = Column(DateTime, default=datetime.utcnow)


def _migrate_sqlite_schema():
    """Простая миграция для SQLite: добавление отсутствующих колонок."""
    with engine.connect() as conn:
        # Проверяем наличие таблицы users
        res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")).fetchone()
        if not res:
            return

        # Читаем схему таблицы
        cols = conn.execute(text("PRAGMA table_info('users');")).fetchall()
        col_names = {row[1] for row in cols}

        # Определяем необходимость полного пересоздания таблицы (сломанная старая схема)
        name_to_type = {row[1]: (row[2] or '').upper() for row in cols}
        needs_rebuild = False
        # Старое поле access_expires_at
        if 'access_expires_at' in col_names:
            needs_rebuild = True
        # id был INTEGER
        id_type = name_to_type.get('id', '')
        if id_type.startswith('INT'):
            needs_rebuild = True
        # totp_secret не бинарный
        secret_type = name_to_type.get('totp_secret', '')
        if secret_type and 'BLOB' not in secret_type:
            needs_rebuild = True

        if needs_rebuild:
            # Переименуем старую таблицу, создадим новую, удалим старую
            conn.execute(text("ALTER TABLE users RENAME TO users_old"))
            conn.commit()
            # Удаляем старые индексы, если остались в sqlite_master
            try:
                conn.execute(text("DROP INDEX IF EXISTS ix_users_username"))
                conn.execute(text("DROP INDEX IF EXISTS ix_users_id"))
                conn.commit()
            except Exception:
                pass
            # Создаем новую таблицу через SQLAlchemy metadata
            Base.metadata.create_all(bind=engine, tables=[User.__table__])
            # Дропаем старую без миграции данных (данные несовместимы)
            conn.execute(text("DROP TABLE IF EXISTS users_old"))
            conn.commit()
        else:
            # Точечная миграция: добавляем столбец secret_expires_at при его отсутствии
            if 'secret_expires_at' not in col_names:
                conn.execute(text("ALTER TABLE users ADD COLUMN secret_expires_at DATETIME"))
                conn.commit()


# Создаем таблицы и выполняем простую миграцию, если нужно
Base.metadata.create_all(bind=engine)
_migrate_sqlite_schema()


def get_db():
    """Получение сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

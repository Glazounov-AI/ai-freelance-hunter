import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/test")
os.environ.setdefault("ADMIN_API_TOKEN", "test-admin-token-1234567890-abcdefgh")

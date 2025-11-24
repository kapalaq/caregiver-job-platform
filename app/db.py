from sqlalchemy import create_engine
import os
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'caregiver_platform',
    'user': 'root',
    'password': 'Ai230592'  # MySQL password
}

# Build connection URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def get_connection():
    with engine.connect() as conn:
        yield conn

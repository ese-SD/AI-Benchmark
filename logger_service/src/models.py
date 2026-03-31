import os

from sqlalchemy import Boolean, Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_HOST = os.getenv("DB_HOST", "perf_db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "perf_db")
DB_USER = os.getenv("DB_USER", "micro_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "micro_pass")
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class TrainingMetric(Base):
    __tablename__ = "training_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_key = Column(String, index=True, nullable=False)
    framework = Column(String, nullable=False)
    dataset = Column(String, nullable=False)
    epoch = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    execution_speed_seconds = Column(Float, nullable=False)
    ram_usage_percent = Column(Float, nullable=False)
    cpu_usage_percent = Column(Float, nullable=False)
    timestamp = Column(Float, nullable=False)


class TrainingResult(Base):
    __tablename__ = "training_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_key = Column(String, unique=True, index=True, nullable=False)
    framework = Column(String, nullable=False)
    dataset = Column(String, nullable=False)
    status = Column(String, nullable=False)
    final_accuracy = Column(Float, nullable=True)
    timestamp = Column(Float, nullable=False)


class AppUser(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)


Base.metadata.create_all(engine)

import hashlib
import os
import time
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_HOST = os.getenv("DB_HOST", "perf_db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "perf_db")
DB_USER = os.getenv("DB_USER", "micro_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "micro_pass")
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AppUser(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)


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


Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TrainingCreateRequest(BaseModel):
    framework: str
    dataset_name: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_token(user_id: int) -> str:
    return f"user-{user_id}"


def parse_token(token: str) -> int:
    if not token.startswith("user-"):
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        return int(token.replace("user-", "").strip())
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def public_user(user: AppUser) -> dict:
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "is_admin": user.is_admin,
    }


def seed_users() -> None:
    db = SessionLocal()
    try:
        if db.query(AppUser).count() > 0:
            return

        users = [
            AppUser(first_name="Admin", last_name="One", username="admin1", password_hash=hash_password("admin123"), is_admin=True),
            AppUser(first_name="Admin", last_name="Two", username="admin2", password_hash=hash_password("admin123"), is_admin=True),
            AppUser(first_name="User", last_name="One", username="user1", password_hash=hash_password("user123"), is_admin=False),
            AppUser(first_name="User", last_name="Two", username="user2", password_hash=hash_password("user123"), is_admin=False),
            AppUser(first_name="User", last_name="Three", username="user3", password_hash=hash_password("user123"), is_admin=False),
        ]
        db.add_all(users)
        db.commit()
    finally:
        db.close()


def get_current_user(authorization: Optional[str]) -> AppUser:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization.replace("Bearer ", "").strip()
    user_id = parse_token(token)

    db = SessionLocal()
    try:
        user = db.query(AppUser).filter(AppUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    finally:
        db.close()


def visible_metrics(rows: list[TrainingMetric], is_admin: bool) -> list[dict]:
    result = []
    for row in rows:
        item = {
            "epoch": row.epoch,
            "accuracy": row.accuracy,
            "execution_speed_seconds": row.execution_speed_seconds,
            "cpu_usage_percent": row.cpu_usage_percent if is_admin else 0.0,
            "ram_usage_percent": row.ram_usage_percent if is_admin else 0.0,
            "timestamp": row.timestamp,
        }
        result.append(item)
    return result


def dataset_display(dataset: str) -> str:
    mapping = {
        "fashion_mnist": "fashion_mnist",
        "fashion-mnist": "fashion_mnist",
        "Fashion-MNIST": "fashion_mnist",
        "cifar100": "cifar100",
        "cifar-100": "cifar100",
        "CIFAR-100": "cifar100",
    }
    return mapping.get(dataset, dataset)


seed_users()


@app.get("/health")
def health():
    return {"status": "ok", "time": time.time()}


@app.post("/auth/register")
def register(payload: RegisterRequest):
    username = payload.username.strip()
    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()
    password = payload.password.strip()

    if not username or not first_name or not last_name or not password:
        raise HTTPException(status_code=400, detail="Tous les champs sont requis")

    db = SessionLocal()
    try:
        existing = db.query(AppUser).filter(AppUser.username.ilike(username)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username déjà utilisé")

        user = AppUser(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password_hash=hash_password(password),
            is_admin=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return public_user(user)
    finally:
        db.close()


@app.post("/auth/login")
def login(payload: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(AppUser).filter(AppUser.username == payload.username).first()
        if not user or user.password_hash != hash_password(payload.password):
            raise HTTPException(status_code=401, detail="Identifiants invalides")

        return {
            "access_token": create_token(user.id),
            "token_type": "bearer",
            "user": public_user(user),
        }
    finally:
        db.close()


@app.get("/auth/me")
def me(authorization: Optional[str] = Header(default=None)):
    user = get_current_user(authorization)
    return public_user(user)


@app.get("/trainings")
def list_trainings(authorization: Optional[str] = Header(default=None)):
    _ = get_current_user(authorization)

    db = SessionLocal()
    try:
        metrics = db.query(TrainingMetric).order_by(TrainingMetric.timestamp.asc()).all()
        results = {item.run_key: item for item in db.query(TrainingResult).all()}

        grouped: dict[str, dict] = {}
        for row in metrics:
            if row.run_key not in grouped:
                grouped[row.run_key] = {
                    "id": row.run_key,
                    "framework": row.framework.lower(),
                    "dataset_name": dataset_display(row.dataset),
                    "status": "running",
                    "final_accuracy": None,
                    "created_by": 1,
                    "created_at": int(row.timestamp * 1000),
                    "latest_timestamp": row.timestamp,
                    "last_accuracy": row.accuracy,
                }
            else:
                grouped[row.run_key]["latest_timestamp"] = max(grouped[row.run_key]["latest_timestamp"], row.timestamp)
                grouped[row.run_key]["last_accuracy"] = row.accuracy

        for run_key, item in grouped.items():
            if run_key in results:
                item["status"] = results[run_key].status
                item["final_accuracy"] = results[run_key].final_accuracy
            else:
                item["final_accuracy"] = item["last_accuracy"]

        runs = list(grouped.values())
        runs.sort(key=lambda item: item["latest_timestamp"], reverse=True)

        for item in runs:
            item.pop("latest_timestamp", None)
            item.pop("last_accuracy", None)

        return runs
    finally:
        db.close()


@app.get("/trainings/{training_id}")
def get_training(training_id: str, authorization: Optional[str] = Header(default=None)):
    _ = get_current_user(authorization)

    db = SessionLocal()
    try:
        metric = (
            db.query(TrainingMetric)
            .filter(TrainingMetric.run_key == training_id)
            .order_by(TrainingMetric.timestamp.desc())
            .first()
        )
        if not metric:
            raise HTTPException(status_code=404, detail="Run introuvable")

        result = db.query(TrainingResult).filter(TrainingResult.run_key == training_id).first()

        return {
            "id": training_id,
            "framework": metric.framework.lower(),
            "dataset_name": dataset_display(metric.dataset),
            "status": result.status if result else "running",
            "final_accuracy": result.final_accuracy if result else metric.accuracy,
            "created_by": 1,
            "created_at": int(metric.timestamp * 1000),
        }
    finally:
        db.close()


@app.get("/trainings/{training_id}/metrics")
def get_training_metrics(training_id: str, authorization: Optional[str] = Header(default=None)):
    user = get_current_user(authorization)

    db = SessionLocal()
    try:
        rows = (
            db.query(TrainingMetric)
            .filter(TrainingMetric.run_key == training_id)
            .order_by(TrainingMetric.timestamp.asc())
            .all()
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Run introuvable")
        return visible_metrics(rows, user.is_admin)
    finally:
        db.close()


@app.post("/trainings")
def create_training(_: TrainingCreateRequest, authorization: Optional[str] = Header(default=None)):
    user = get_current_user(authorization)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Réservé aux admins")
    raise HTTPException(
        status_code=405,
        detail="Les benchmarks démarrent automatiquement au lancement des workers dans cette version.",
    )

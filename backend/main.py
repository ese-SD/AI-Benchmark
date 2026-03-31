from copy import deepcopy
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


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


def create_token(user_id: int) -> str:
    return f"user-{user_id}"


def parse_token(token: str) -> int:
    if not token.startswith("user-"):
        raise HTTPException(status_code=401, detail="Invalid token")

    raw_id = token.replace("user-", "").strip()

    try:
        return int(raw_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "username": user["username"],
        "is_admin": user["is_admin"],
    }


def get_current_user(authorization: Optional[str]) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = authorization.replace("Bearer ", "").strip()
    user_id = parse_token(token)

    for user in STATE["users"]:
        if user["id"] == user_id:
            return user

    raise HTTPException(status_code=401, detail="User not found")


def build_metric_script(framework: str, dataset_name: str) -> list[dict]:
    is_torch = framework == "pytorch"

    if dataset_name == "cifar100":
        return [
            {
                "epoch": 1,
                "accuracy": 18 if is_torch else 15,
                "execution_speed_seconds": 1.9 if is_torch else 2.1,
                "cpu_usage_percent": 28,
                "ram_usage_percent": 34,
            },
            {
                "epoch": 2,
                "accuracy": 27 if is_torch else 23,
                "execution_speed_seconds": 1.8 if is_torch else 2.0,
                "cpu_usage_percent": 31,
                "ram_usage_percent": 36,
            },
            {
                "epoch": 3,
                "accuracy": 35 if is_torch else 31,
                "execution_speed_seconds": 1.8 if is_torch else 1.9,
                "cpu_usage_percent": 35,
                "ram_usage_percent": 39,
            },
            {
                "epoch": 4,
                "accuracy": 42 if is_torch else 38,
                "execution_speed_seconds": 1.7 if is_torch else 1.9,
                "cpu_usage_percent": 39,
                "ram_usage_percent": 42,
            },
            {
                "epoch": 5,
                "accuracy": 48 if is_torch else 44,
                "execution_speed_seconds": 1.7 if is_torch else 1.8,
                "cpu_usage_percent": 43,
                "ram_usage_percent": 45,
            },
        ]

    return [
        {
            "epoch": 1,
            "accuracy": 62 if is_torch else 58,
            "execution_speed_seconds": 1.2 if is_torch else 1.4,
            "cpu_usage_percent": 22,
            "ram_usage_percent": 26,
        },
        {
            "epoch": 2,
            "accuracy": 71 if is_torch else 67,
            "execution_speed_seconds": 1.1 if is_torch else 1.3,
            "cpu_usage_percent": 26,
            "ram_usage_percent": 29,
        },
        {
            "epoch": 3,
            "accuracy": 79 if is_torch else 75,
            "execution_speed_seconds": 1.1 if is_torch else 1.2,
            "cpu_usage_percent": 29,
            "ram_usage_percent": 32,
        },
        {
            "epoch": 4,
            "accuracy": 84 if is_torch else 81,
            "execution_speed_seconds": 1.0 if is_torch else 1.2,
            "cpu_usage_percent": 33,
            "ram_usage_percent": 35,
        },
        {
            "epoch": 5,
            "accuracy": 88 if is_torch else 86,
            "execution_speed_seconds": 1.0 if is_torch else 1.1,
            "cpu_usage_percent": 36,
            "ram_usage_percent": 37,
        },
    ]


def sanitize_run(run: dict) -> dict:
    return {
        "id": run["id"],
        "framework": run["framework"],
        "dataset_name": run["dataset_name"],
        "status": run["status"],
        "final_accuracy": run["final_accuracy"],
        "created_by": run["created_by"],
        "created_at": run["created_at"],
    }


def visible_metrics(metrics: list[dict], is_admin: bool) -> list[dict]:
    if is_admin:
        return deepcopy(metrics)

    filtered = []
    for metric in metrics:
        filtered.append(
            {
                "epoch": metric["epoch"],
                "accuracy": metric["accuracy"],
                "execution_speed_seconds": metric["execution_speed_seconds"],
                "cpu_usage_percent": 0,
                "ram_usage_percent": 0,
            }
        )
    return filtered


def advance_run(run: dict) -> None:
    if run["status"] != "running":
        return

    current_count = len(run["metrics"])
    total_count = len(run["metrics_script"])

    if current_count < total_count:
        run["metrics"].append(deepcopy(run["metrics_script"][current_count]))

    if len(run["metrics"]) >= total_count:
        run["status"] = "finished"
        run["final_accuracy"] = run["metrics"][-1]["accuracy"]


def create_seed_runs() -> list[dict]:
    finished_script = build_metric_script("pytorch", "fashion_mnist")
    running_script = build_metric_script("tensorflow", "cifar100")

    return [
        {
            "id": 1,
            "framework": "pytorch",
            "dataset_name": "fashion_mnist",
            "status": "finished",
            "final_accuracy": finished_script[-1]["accuracy"],
            "created_by": 1,
            "created_at": 1710000000000,
            "metrics": deepcopy(finished_script),
            "metrics_script": deepcopy(finished_script),
        },
        {
            "id": 2,
            "framework": "tensorflow",
            "dataset_name": "cifar100",
            "status": "running",
            "final_accuracy": None,
            "created_by": 1,
            "created_at": 1710000100000,
            "metrics": deepcopy(running_script[:2]),
            "metrics_script": deepcopy(running_script),
        },
    ]


STATE = {
    "next_user_id": 6,
    "next_run_id": 3,
    "users": [
        {
            "id": 1,
            "first_name": "Admin",
            "last_name": "One",
            "username": "admin1",
            "password": "admin123",
            "is_admin": True,
        },
        {
            "id": 2,
            "first_name": "Admin",
            "last_name": "Two",
            "username": "admin2",
            "password": "admin123",
            "is_admin": True,
        },
        {
            "id": 3,
            "first_name": "User",
            "last_name": "One",
            "username": "user1",
            "password": "user123",
            "is_admin": False,
        },
        {
            "id": 4,
            "first_name": "User",
            "last_name": "Two",
            "username": "user2",
            "password": "user123",
            "is_admin": False,
        },
        {
            "id": 5,
            "first_name": "User",
            "last_name": "Three",
            "username": "user3",
            "password": "user123",
            "is_admin": False,
        },
    ],
    "runs": create_seed_runs(),
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/register")
def register(payload: RegisterRequest):
    username = payload.username.strip()
    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()
    password = payload.password

    if not username or not first_name or not last_name or not password:
        raise HTTPException(status_code=400, detail="Tous les champs sont requis")

    for user in STATE["users"]:
        if user["username"].lower() == username.lower():
            raise HTTPException(status_code=400, detail="Username déjà utilisé")

    new_user = {
        "id": STATE["next_user_id"],
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "password": password,
        "is_admin": False,
    }

    STATE["next_user_id"] += 1
    STATE["users"].append(new_user)

    return public_user(new_user)


@app.post("/auth/login")
def login(payload: LoginRequest):
    for user in STATE["users"]:
        if user["username"] == payload.username and user["password"] == payload.password:
            return {
                "access_token": create_token(user["id"]),
                "token_type": "bearer",
                "user": public_user(user),
            }

    raise HTTPException(status_code=401, detail="Identifiants invalides")


@app.get("/auth/me")
def me(authorization: Optional[str] = Header(default=None)):
    user = get_current_user(authorization)
    return public_user(user)


@app.get("/trainings")
def list_trainings(authorization: Optional[str] = Header(default=None)):
    _ = get_current_user(authorization)

    runs = sorted(STATE["runs"], key=lambda run: run["id"], reverse=True)
    return [sanitize_run(run) for run in runs]


@app.get("/trainings/{training_id}")
def get_training(training_id: int, authorization: Optional[str] = Header(default=None)):
    _ = get_current_user(authorization)

    for run in STATE["runs"]:
        if run["id"] == training_id:
            return sanitize_run(run)

    raise HTTPException(status_code=404, detail="Run introuvable")


@app.get("/trainings/{training_id}/metrics")
def get_training_metrics(training_id: int, authorization: Optional[str] = Header(default=None)):
    user = get_current_user(authorization)

    for run in STATE["runs"]:
        if run["id"] == training_id:
            advance_run(run)
            return visible_metrics(run["metrics"], user["is_admin"])

    raise HTTPException(status_code=404, detail="Run introuvable")


@app.post("/trainings")
def create_training(payload: TrainingCreateRequest, authorization: Optional[str] = Header(default=None)):
    user = get_current_user(authorization)

    if not user["is_admin"]:
        raise HTTPException(status_code=403, detail="Réservé aux admins")

    framework = payload.framework or "pytorch"
    dataset_name = payload.dataset_name or "fashion_mnist"

    new_run = {
        "id": STATE["next_run_id"],
        "framework": framework,
        "dataset_name": dataset_name,
        "status": "running",
        "final_accuracy": None,
        "created_by": user["id"],
        "created_at": 1710000200000 + STATE["next_run_id"] * 1000,
        "metrics": [],
        "metrics_script": build_metric_script(framework, dataset_name),
    }

    STATE["next_run_id"] += 1
    STATE["runs"].append(new_run)

    return sanitize_run(new_run)
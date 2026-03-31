import json
import os
import time

from confluent_kafka import Consumer
from sqlalchemy.exc import OperationalError

from models import Session, TrainingMetric, TrainingResult

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "training_data")

consumer_config = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "group.id": "tracker",
    "auto.offset.reset": "earliest",
}


def wait_for_db(max_attempts: int = 30, sleep_seconds: int = 2) -> None:
    for attempt in range(1, max_attempts + 1):
        try:
            session = Session()
            session.execute("SELECT 1")
            session.close()
            print("Database is ready", flush=True)
            return
        except OperationalError:
            print(f"Database not ready yet ({attempt}/{max_attempts})", flush=True)
            time.sleep(sleep_seconds)
    raise RuntimeError("Database unavailable")


def upsert_result(session, payload: dict) -> None:
    existing = session.query(TrainingResult).filter(TrainingResult.run_key == payload["run_key"]).first()
    if existing:
        existing.status = payload.get("status", existing.status)
        existing.final_accuracy = payload.get("final_accuracy", existing.final_accuracy)
        existing.timestamp = payload.get("timestamp", existing.timestamp)
        return

    session.add(
        TrainingResult(
            run_key=payload["run_key"],
            framework=payload["framework"],
            dataset=payload["dataset"],
            status=payload.get("status", "finished"),
            final_accuracy=payload.get("final_accuracy"),
            timestamp=payload.get("timestamp", time.time()),
        )
    )


def main() -> None:
    wait_for_db()

    consumer = Consumer(consumer_config)
    consumer.subscribe([KAFKA_TOPIC])
    print("Logger consumer is running", flush=True)

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}", flush=True)
                continue

            payload = json.loads(msg.value().decode("utf-8"))
            print(f"Consumed: {payload}", flush=True)

            session = Session()
            try:
                event_type = payload.get("event_type", "metric")
                if event_type == "metric":
                    session.add(
                        TrainingMetric(
                            run_key=payload["run_key"],
                            framework=payload["framework"],
                            dataset=payload["dataset"],
                            epoch=payload["epoch"],
                            accuracy=payload["accuracy"],
                            execution_speed_seconds=payload["execution_speed_seconds"],
                            ram_usage_percent=payload["ram_usage_percent"],
                            cpu_usage_percent=payload["cpu_usage_percent"],
                            timestamp=payload.get("timestamp", time.time()),
                        )
                    )
                elif event_type == "result":
                    upsert_result(session, payload)
                session.commit()
            finally:
                session.close()
    except KeyboardInterrupt:
        print("Stopping consumer", flush=True)
    finally:
        consumer.close()


if __name__ == "__main__":
    main()

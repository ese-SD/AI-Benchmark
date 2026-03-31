from confluent_kafka import Producer
import json
import time

print("kafka is ready")

producer = Producer({'bootstrap.servers':'kafka:9092'})

def delivery_report(err, msg):
    if err:
        print(f"Delivery failed {err}", flush=True)
    else:
        value = msg.value().decode("utf-8")
        print(f"Delivered {value}", flush=True)
        print(f"To {msg.topic()}", flush=True)

training_metrics = {
    "framework": "PyTorch",
    "dataset": "Fashion-MNIST",
    "epoch": 1,
    "accuracy": 75.5,
    "execution_speed_seconds": 12.6,
    "cpu_usage_percent": 85.2,
    "ram_usage_percent": 56.7,
    "timestamp": time.time()
}

while True:
    producer.produce(topic='training_data',
                    value=json.dumps(training_metrics).encode("utf-8"),
                    callback=delivery_report)

    producer.flush()
    time.sleep(1)


import gzip
import json
import os
import pickle
import time

import numpy as np
import psutil
from confluent_kafka import Producer
from tensorflow import keras

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "training_data")
EPOCHS = int(os.getenv("EPOCHS", "2"))
MAX_BATCHES_PER_EPOCH = int(os.getenv("MAX_BATCHES_PER_EPOCH", "30"))
METRIC_EVERY_N_BATCHES = int(os.getenv("METRIC_EVERY_N_BATCHES", "10"))

producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})


def delivery_report(err, msg):
    if err:
        print(f"Delivery failed: {err}", flush=True)


def normalize_framework() -> str:
    return "tensorflow"


def run_key(dataset: str) -> str:
    return f"{normalize_framework()}-{dataset.lower().replace('_', '-')}"


def send_event(payload: dict):
    producer.produce(
        topic=KAFKA_TOPIC,
        value=json.dumps(payload).encode("utf-8"),
        callback=delivery_report,
    )
    producer.flush()
    print(f"[KAFKA TensorFlow] {json.dumps(payload)}", flush=True)


class KafkaMetricsCallback(keras.callbacks.Callback):
    def __init__(self, dataset_name: str):
        super().__init__()
        self.dataset_name = dataset_name
        self.current_epoch = 1
        self.batch_count = 0
        self.start_time = time.time()
        self.last_accuracy = 0.0

    def on_epoch_begin(self, epoch, logs=None):
        self.current_epoch = epoch + 1

    def on_train_batch_end(self, batch, logs=None):
        self.batch_count += 1
        accuracy = round(float(logs.get("accuracy", 0)) * 100, 2)
        self.last_accuracy = accuracy
        if self.batch_count % METRIC_EVERY_N_BATCHES == 0:
            speed = time.time() - self.start_time
            send_event(
                {
                    "event_type": "metric",
                    "run_key": run_key(self.dataset_name),
                    "framework": normalize_framework(),
                    "dataset": self.dataset_name,
                    "epoch": self.current_epoch,
                    "accuracy": accuracy,
                    "execution_speed_seconds": round(speed, 2),
                    "cpu_usage_percent": psutil.cpu_percent(),
                    "ram_usage_percent": psutil.virtual_memory().percent,
                    "timestamp": time.time(),
                }
            )
            self.start_time = time.time()

    def on_train_end(self, logs=None):
        send_event(
            {
                "event_type": "result",
                "run_key": run_key(self.dataset_name),
                "framework": normalize_framework(),
                "dataset": self.dataset_name,
                "status": "finished",
                "final_accuracy": self.last_accuracy,
                "timestamp": time.time(),
            }
        )


def build_simple_cnn():
    return keras.Sequential([
        keras.Input(shape=(28, 28, 1)),
        keras.layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
        keras.layers.MaxPooling2D(pool_size=(2, 2)),
        keras.layers.Flatten(),
        keras.layers.Dense(10, activation="softmax"),
    ])


def build_resnet_model():
    base_model = keras.applications.ResNet50(include_top=False, weights=None, input_shape=(32, 32, 3))
    return keras.Sequential([
        base_model,
        keras.layers.GlobalAveragePooling2D(),
        keras.layers.Dense(100, activation="softmax"),
    ])


def load_fashion_mnist_raw(path, kind="train"):
    labels_path = os.path.join(path, f"{kind}-labels-idx1-ubyte.gz")
    images_path = os.path.join(path, f"{kind}-images-idx3-ubyte.gz")
    with gzip.open(labels_path, "rb") as lbpath:
        labels = np.frombuffer(lbpath.read(), dtype=np.uint8, offset=8)
    with gzip.open(images_path, "rb") as imgpath:
        images = np.frombuffer(imgpath.read(), dtype=np.uint8, offset=16).reshape(len(labels), 28, 28)
    return images, labels


def train_tensorflow_on_fashion_mnist():
    print("Starting TensorFlow on Fashion MNIST", flush=True)
    raw_path = "/data/datasets/FashionMNIST/raw"
    x_train, y_train = load_fashion_mnist_raw(raw_path, kind="train")
    x_train = x_train.astype("float32") / 255.0
    x_train = np.expand_dims(x_train, -1)

    model = build_simple_cnn()
    model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
    model.fit(
        x_train,
        y_train,
        batch_size=128,
        epochs=EPOCHS,
        steps_per_epoch=MAX_BATCHES_PER_EPOCH,
        callbacks=[KafkaMetricsCallback("fashion_mnist")],
        verbose=0,
    )


def train_tensorflow_on_cifar100():
    print("Starting TensorFlow on CIFAR-100", flush=True)
    with open("/data/datasets/cifar-100-python/train", "rb") as file_handle:
        dict_cifar = pickle.load(file_handle, encoding="bytes")
        x_train = dict_cifar[b"data"]
        y_train = np.array(dict_cifar[b"fine_labels"])

    x_train = x_train.reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1)
    x_train = x_train.astype("float32") / 255.0
    x_train = (x_train - 0.5) / 0.5

    model = build_resnet_model()
    model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
    model.fit(
        x_train,
        y_train,
        batch_size=128,
        epochs=EPOCHS,
        steps_per_epoch=MAX_BATCHES_PER_EPOCH,
        callbacks=[KafkaMetricsCallback("cifar100")],
        verbose=0,
    )


def main():
    os.makedirs("/data/datasets", exist_ok=True)
    train_tensorflow_on_fashion_mnist()
    train_tensorflow_on_cifar100()
    print("TensorFlow finished all trainings", flush=True)


if __name__ == "__main__":
    main()

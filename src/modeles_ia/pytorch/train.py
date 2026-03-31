import json
import os
import time

import psutil
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from confluent_kafka import Producer

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
    return "pytorch"


def run_key(dataset: str) -> str:
    return f"{normalize_framework()}-{dataset.lower().replace('_', '-')}"


def send_event(payload: dict):
    producer.produce(
        topic=KAFKA_TOPIC,
        value=json.dumps(payload).encode("utf-8"),
        callback=delivery_report,
    )
    producer.flush()
    print(f"[KAFKA PyTorch] {json.dumps(payload)}", flush=True)


class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(32 * 13 * 13, 10)

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.flatten(x)
        x = self.fc(x)
        return x


def get_resnet_model():
    return torchvision.models.resnet18(num_classes=100)


def train_on_dataset(dataset_label: str, trainloader, model, criterion, optimizer):
    last_accuracy = 0.0

    for epoch in range(EPOCHS):
        correct, total = 0, 0
        start_time = time.time()

        for i, batch_data in enumerate(trainloader, 0):
            if i >= MAX_BATCHES_PER_EPOCH:
                break

            inputs, labels = batch_data
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            if (i + 1) % METRIC_EVERY_N_BATCHES == 0:
                speed = time.time() - start_time
                last_accuracy = round(100 * correct / max(total, 1), 2)
                send_event(
                    {
                        "event_type": "metric",
                        "run_key": run_key(dataset_label),
                        "framework": normalize_framework(),
                        "dataset": dataset_label,
                        "epoch": epoch + 1,
                        "accuracy": last_accuracy,
                        "execution_speed_seconds": round(speed, 2),
                        "cpu_usage_percent": psutil.cpu_percent(),
                        "ram_usage_percent": psutil.virtual_memory().percent,
                        "timestamp": time.time(),
                    }
                )
                correct, total, start_time = 0, 0, time.time()

    send_event(
        {
            "event_type": "result",
            "run_key": run_key(dataset_label),
            "framework": normalize_framework(),
            "dataset": dataset_label,
            "status": "finished",
            "final_accuracy": last_accuracy,
            "timestamp": time.time(),
        }
    )


def train_pytorch_on_fashion_mnist():
    print("Starting PyTorch on Fashion MNIST", flush=True)
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,)),
    ])
    trainset = torchvision.datasets.FashionMNIST(
        root="/data/datasets",
        train=True,
        download=False,
        transform=transform,
    )
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=128, shuffle=True)
    model = SimpleCNN()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    train_on_dataset("fashion_mnist", trainloader, model, criterion, optimizer)


def train_pytorch_on_cifar100():
    print("Starting PyTorch on CIFAR-100", flush=True)
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])
    trainset = torchvision.datasets.CIFAR100(
        root="/data/datasets",
        train=True,
        download=False,
        transform=transform,
    )
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=128, shuffle=True)
    model = get_resnet_model()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    train_on_dataset("cifar100", trainloader, model, criterion, optimizer)


def main():
    train_pytorch_on_fashion_mnist()
    train_pytorch_on_cifar100()
    print("PyTorch finished all trainings", flush=True)


if __name__ == "__main__":
    main()

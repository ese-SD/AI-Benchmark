import os
import time
import json
import psutil
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms

def send_metrics(metrics):
    """
    Simulation de l'envoi Kafka. 
    Pour l'instant, on affiche juste le JSON dans la console du conteneur.
    """
    print(f"[MÉTRIQUES PyTorch] {json.dumps(metrics)}")


# Architecture simple pour Fashion MNIST, et ResNet18 pour CIFAR-100
class SimpleCNN(nn.Module):
    """Architecture simple pour Fashion MNIST"""
    def __init__(self):
        super(SimpleCNN, self).__init__()
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
    """Charge l'architecture ResNet18 standard pour CIFAR-100"""
    return torchvision.models.resnet18(num_classes=100)


# Fonctions d'entraînement
def train_PyTorch_on_fashion_mnist():
    print("\n--- Entrainement de PyTorch sur Fashion MNIST ---")
    
    data = np.load('/data/datasets/fashion-mnist.npz')
    x_train = data['x_train'].astype(np.float32) / 255.0
    x_train = np.expand_dims(x_train, 1) # Format: (Batch, Channel, H, W)
    y_train = data['y_train'].astype(np.int64)

    dataset = torch.utils.data.TensorDataset(torch.Tensor(x_train), torch.Tensor(y_train).long())
    trainloader = torch.utils.data.DataLoader(dataset, batch_size=128, shuffle=True)

    model = SimpleCNN()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(5): 
        correct, total = 0, 0
        start_time = time.time()
        
        for i, batch_data in enumerate(trainloader, 0):
            inputs, labels = batch_data
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            if i % 20 == 19:
                speed = time.time() - start_time
                send_metrics({
                    "framework": "PyTorch", "dataset": "Fashion-MNIST",
                    "epoch": epoch + 1, "accuracy": round(100 * correct / total, 2),
                    "execution_speed_seconds": round(speed, 2),
                    "cpu_usage_percent": psutil.cpu_percent(),
                    "ram_usage_percent": psutil.virtual_memory().percent,
                    "timestamp": time.time()
                })
                correct, total, start_time = 0, 0, time.time()

def train_PyTorch_on_cifar100():
    print("\n--- Entrainement de PyTorch sur CIFAR-100 ---")
    
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    
    trainset = torchvision.datasets.CIFAR100(root='/data/datasets/', train=True, download=False, transform=transform)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=128, shuffle=True)

    model = get_resnet_model()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

    for epoch in range(5):
        correct, total = 0, 0
        start_time = time.time()
        
        for i, batch_data in enumerate(trainloader, 0):
            inputs, labels = batch_data
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            if i % 20 == 19:
                speed = time.time() - start_time
                send_metrics({
                    "framework": "PyTorch", "dataset": "CIFAR-100",
                    "epoch": epoch + 1, "accuracy": round(100 * correct / total, 2),
                    "execution_speed_seconds": round(speed, 2),
                    "cpu_usage_percent": psutil.cpu_percent(),
                    "ram_usage_percent": psutil.virtual_memory().percent,
                    "timestamp": time.time()
                })
                correct, total, start_time = 0, 0, time.time()


def main():
    os.makedirs('/data/datasets', exist_ok=True)
    train_PyTorch_on_fashion_mnist()
    train_PyTorch_on_cifar100()
    print("\n PyTorch a terminé tous ses entraînements.")

if __name__ == "__main__":
    main()
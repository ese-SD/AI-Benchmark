import os
import time
import json
import psutil
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

def main():
    # Création du dossier si le volume n'est pas encore bien monté
    os.makedirs('/data/datasets', exist_ok=True)

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    
    print("Chargement de CIFAR-100 depuis /data/datasets/...")

    trainset = torchvision.datasets.CIFAR100(
        root='/data/datasets/', 
        train=True, 
        download=False, 
        transform=transform
    )    
    
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=128, shuffle=True)

    model = torchvision.models.resnet18(num_classes=100)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

    print("Début de l'entraînement PyTorch...")
    
    for epoch in range(10):
        correct = 0
        total = 0
        dino_timer_start = time.time()  # Chrono pour la vitesse d'exécution
        
        for i, data in enumerate(trainloader, 0):
            inputs, labels = data
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            # Extraction et affichage des métriques toutes les 20 itérations
            if i % 20 == 19:
                speed = time.time() - dino_timer_start
                accuracy = 100 * correct / total
                
                metrics = {
                    "framework": "PyTorch",
                    "dataset": "CIFAR-100",
                    "epoch": epoch + 1,
                    "accuracy": round(accuracy, 2),
                    "execution_speed_seconds": round(speed, 2),
                    "cpu_usage_percent": psutil.cpu_percent(),
                    "ram_usage_percent": psutil.virtual_memory().percent,
                    "timestamp": time.time()
                }
                
                send_metrics(metrics)
                
                # Reset des compteurs
                correct = 0
                total = 0
                dino_timer_start = time.time()

if __name__ == "__main__":
    main()
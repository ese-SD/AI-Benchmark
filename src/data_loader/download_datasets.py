import os
from torchvision import datasets

DATA_DIR = "/data/datasets"

os.makedirs(DATA_DIR, exist_ok=True)

print("Downloading CIFAR100...")
datasets.CIFAR100(root=DATA_DIR, train=True, download=True)

print("Downloading FashionMNIST...")
datasets.FashionMNIST(root=DATA_DIR, train=True, download=True)

print("Datasets ready.")
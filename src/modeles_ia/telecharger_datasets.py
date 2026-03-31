import os
import urllib.request
import tarfile
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

DATASETS_DIR = '/data/datasets'

def download_fashion_mnist():
    print("\n--- Téléchargement de Fashion MNIST ---")
    npz_url = "https://storage.googleapis.com/tensorflow/tf-keras-datasets/fashion-mnist.npz"
    dest_path = os.path.join(DATASETS_DIR, "fashion-mnist.npz")
    
    if os.path.exists(dest_path):
        print(" Fashion MNIST est déjà présent.")
        return

    urllib.request.urlretrieve(npz_url, dest_path)
    print("Fashion MNIST téléchargé avec succès !")

def download_cifar100():
    print("\n--- Téléchargement de CIFAR-100 ---")
    url = "https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz"
    tar_path = os.path.join(DATASETS_DIR, "cifar-100-python.tar.gz")
    extract_dir = os.path.join(DATASETS_DIR, "cifar-100-python")
    
    if os.path.exists(extract_dir):
        print("CIFAR-100 est déjà présent.")
        return

    print("Téléchargement de l'archive (environ 160 Mo)...")
    urllib.request.urlretrieve(url, tar_path)
    
    print("Extraction en cours...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=DATASETS_DIR)
        
    print("CIFAR-100 extrait avec succès !")

if __name__ == "__main__":
    os.makedirs(DATASETS_DIR, exist_ok=True)
    download_fashion_mnist()
    download_cifar100()
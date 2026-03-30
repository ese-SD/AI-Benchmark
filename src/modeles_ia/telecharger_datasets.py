import os
import urllib.request
import tarfile


# On définit le chemin absolu vers le dossier data/datasets à la racine du projet
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATASETS_DIR = os.path.join(BASE_DIR, 'data', 'datasets')


def download_fashion_mnist():
    print("\n--- Récupération de Fashion MNIST ---")
    url = "https://storage.googleapis.com/tensorflow/tf-keras-datasets/train-labels-idx1-ubyte.gz"
    # Keras télécharge un fichier .npz par défaut, on va le récupérer directement
    npz_url = "https://storage.googleapis.com/tensorflow/tf-keras-datasets/fashion-mnist.npz"
    dest_path = os.path.join(DATASETS_DIR, "fashion-mnist.npz")
    
    if os.path.exists(dest_path):
        print("Fashion MNIST est déjà présent.")
        return

    print(f"Téléchargement depuis {npz_url}...")
    urllib.request.urlretrieve(npz_url, dest_path)
    print("Fashion MNIST téléchargé avec succès !")

def download_cifar100():
    print("\n--- Récupération de CIFAR-100 ---")
    # PyTorch utilise le tar.gz officiel
    url = "https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz"
    tar_path = os.path.join(DATASETS_DIR, "cifar-100-python.tar.gz")
    extract_dir = os.path.join(DATASETS_DIR, "cifar-100-python")
    
    if os.path.exists(extract_dir) or os.path.exists(tar_path):
        print("CIFAR-100 est déjà présent.")
        return

    print(f"Téléchargement depuis {url} (cela peut prendre quelques minutes)...")
    urllib.request.urlretrieve(url, tar_path)
    
    print("Extraction de l'archive CIFAR-100...")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=DATASETS_DIR)
        
    print("CIFAR-100 téléchargé et extrait avec succès !")

if __name__ == "__main__":
    print(f"Initialisation du volume de données dans : {DATASETS_DIR}")
    
    # Création du dossier s'il n'existe pas
    os.makedirs(DATASETS_DIR, exist_ok=True)
    
    download_fashion_mnist()
    download_cifar100()
    
    print("\n✅ Tous les datasets sont prêts dans le dossier /data/datasets/")
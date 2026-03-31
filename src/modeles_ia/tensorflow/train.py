import gzip
import os
import time
import json
import pickle
import psutil
import numpy as np
from tensorflow import keras



class ConsoleMetricsCallback(keras.callbacks.Callback):
    """Intercepte les métriques Keras en temps réel"""
    def __init__(self, dataset_name):
        super().__init__()
        self.dataset_name = dataset_name
        self.start_time = time.time()
        self.batch_count = 0
        self.current_epoch = 1

    def on_epoch_begin(self, epoch, logs=None):
        self.current_epoch = epoch + 1

    def on_train_batch_end(self, batch, logs=None):
        self.batch_count += 1
        if self.batch_count % 20 == 0:
            speed = time.time() - self.start_time
            metrics = {
                "framework": "TensorFlow",
                "dataset": self.dataset_name,
                "epoch": self.current_epoch,
                "accuracy": round(logs.get('accuracy', 0) * 100, 2),
                "execution_speed_seconds": round(speed, 2),
                "cpu_usage_percent": psutil.cpu_percent(),
                "ram_usage_percent": psutil.virtual_memory().percent,
                "timestamp": time.time()
            }
            print(f"[MÉTRIQUES TensorFlow] {json.dumps(metrics)}")
            self.start_time = time.time()


# Architecture simple pour Fashion MNIST, et ResNet18 pour CIFAR-100

def build_simple_cnn():
    """Architecture simple équivalente pour Fashion MNIST"""
    return keras.Sequential([
        keras.Input(shape=(28, 28, 1)),
        keras.layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
        keras.layers.MaxPooling2D(pool_size=(2, 2)),
        keras.layers.Flatten(),
        keras.layers.Dense(10, activation="softmax"),
    ])

def build_resnet_model():
    """Architecture ResNet50 pour CIFAR-100"""
    base_model = keras.applications.ResNet50(include_top=False, weights=None, input_shape=(32, 32, 3))
    return keras.Sequential([
        base_model,
        keras.layers.GlobalAveragePooling2D(),
        keras.layers.Dense(100, activation="softmax")
    ])

def load_fashion_mnist_raw(path, kind='train'):
    labels_path = os.path.join(path, f'{kind}-labels-idx1-ubyte.gz')
    images_path = os.path.join(path, f'{kind}-images-idx3-ubyte.gz')
    
    with gzip.open(labels_path, 'rb') as lbpath:
        labels = np.frombuffer(lbpath.read(), dtype=np.uint8, offset=8)
    with gzip.open(images_path, 'rb') as imgpath:
        images = np.frombuffer(imgpath.read(), dtype=np.uint8, offset=16).reshape(len(labels), 28, 28)
        
    return images, labels

# Fonctions d'entraînement
def train_tensorflow_on_fashion_mnist():
    print("\n--- Entraînement de TensorFlow sur Fashion MNIST ---")
    
    raw_path = "/data/datasets/FashionMNIST/raw"
    x_train, y_train = load_fashion_mnist_raw(raw_path, kind='train')
    
    x_train = x_train.astype("float32") / 255.0
    x_train = np.expand_dims(x_train, -1)

    model = build_simple_cnn()
    model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
    
    model.fit(
        x_train, y_train, 
        batch_size=128, epochs=5, 
        callbacks=[ConsoleMetricsCallback("Fashion-MNIST")], verbose=0
    )

def train_tensorflow_on_cifar100():
    print("\n--- Entraînement de TensorFlow sur CIFAR-100 ---")
    
    with open('/data/datasets/cifar-100-python/train', 'rb') as f:
        dict_cifar = pickle.load(f, encoding='bytes')
        x_train = dict_cifar[b'data']
        y_train = np.array(dict_cifar[b'fine_labels'])

    x_train = x_train.reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1)
    x_train = x_train.astype("float32") / 255.0
    x_train = (x_train - 0.5) / 0.5 # Normalisation

    model = build_resnet_model()
    model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
    
    model.fit(
        x_train, y_train, 
        batch_size=128, epochs=5, 
        callbacks=[ConsoleMetricsCallback("CIFAR-100")], verbose=0
    )


def main():
    os.makedirs('/data/datasets', exist_ok=True)
    train_tensorflow_on_fashion_mnist()
    train_tensorflow_on_cifar100()
    print("\nTensorFlow a terminé tous ses entraînements.")

if __name__ == "__main__":
    main()
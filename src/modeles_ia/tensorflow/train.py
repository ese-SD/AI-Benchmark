import os
import time
import json
import psutil
import tensorflow as tf
from tensorflow import keras
import numpy as np

class ConsoleMetricsCallback(keras.callbacks.Callback):
    """
    Remplace temporairement le callback Kafka par un simple print()
    """
    def __init__(self):
        super().__init__()
        self.dino_step_time = time.time()
        self.batch_count = 0

    def on_train_batch_end(self, batch, logs=None):
        self.batch_count += 1
        
        # Affichage toutes les 20 itérations
        if self.batch_count % 20 == 0:
            speed = time.time() - self.dino_step_time
            
            metrics = {
                "framework": "TensorFlow",
                "dataset": "Fashion-MNIST",
                # On récupère l'époque actuelle depuis self.params
                "epoch": 1, # Géré approximativement pour cet exemple de callback par batch
                "accuracy": round(logs.get('accuracy', 0) * 100, 2),
                "execution_speed_seconds": round(speed, 2),
                "cpu_usage_percent": psutil.cpu_percent(),
                "ram_usage_percent": psutil.virtual_memory().percent,
                "timestamp": time.time()
            }
            
            print(f"[MÉTRIQUES TF] {json.dumps(metrics)}")
            self.dino_step_time = time.time() # Reset du chrono

def main():
    os.makedirs('/data/datasets', exist_ok=True)
    print("Chargement de Fashion MNIST...")
    
    dataset_path = "/data/datasets/fashion-mnist.npz"
    print(f"Chargement de Fashion MNIST depuis {dataset_path}...")
    
    with np.load(dataset_path) as data:
        x_train = data['x_train']
        y_train = data['y_train']
    
    x_train = x_train.astype("float32") / 255.0
    x_train = np.expand_dims(x_train, -1)

    model = keras.Sequential([
        keras.Input(shape=(28, 28, 1)),
        keras.layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
        keras.layers.MaxPooling2D(pool_size=(2, 2)),
        keras.layers.Flatten(),
        keras.layers.Dense(10, activation="softmax"),
    ])

    model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

    print("Début de l'entraînement TensorFlow...")
    
    # On utilise notre callback qui fait des prints
    console_cb = ConsoleMetricsCallback()
    
    model.fit(
        x_train, y_train, 
        batch_size=128, 
        epochs=10, 
        callbacks=[console_cb],
        verbose=1
    )

if __name__ == "__main__":
    main()
from confluent_kafka import Consumer
import json
from models import *

consumer_config = {
    'bootstrap.servers':'kafka:9092',
    'group.id': "tracker",
    'auto.offset.reset': "earliest"
}

consumer = Consumer(consumer_config)
consumer.subscribe(["training_data"])

print("Consumer is running", flush=True)

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Error !!", flush=True)
            continue
        value = msg.value().decode("utf-8")
        content = json.loads(value)

        print(f"Consumer receive : {content}", flush=True)

        metric = Training_metrics(
            library=content["library"],
            dataset=content["dataset"],
            epoch=content["epoch"],

            accuracy=content["accuracy"],
            duree=content["duree"],
            ram_usage=content["ram_usage"],
            cpu_usage=content["cpu_usage"]
        )
        session.add(metric)
        session.commit()

except KeyboardInterrupt:
    print("Stopping consumer")

finally:
    consumer.close()
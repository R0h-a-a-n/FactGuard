from kafka import KafkaConsumer, KafkaProducer
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import time

def safe_deserialize(v):
    try:
        return json.loads(v.decode("utf-8"))
    except Exception:
        return None

consumer = KafkaConsumer(
    "raw_comments_stream",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="latest",
    value_deserializer=safe_deserialize,
    enable_auto_commit=True,
    group_id="topic-modeler-group"
)

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

print("Consumer A: Topic modeler is running...")

buffer = []
BATCH_SIZE = 10

while True:
    try:
        msg = consumer.poll(timeout_ms=1000)

        for _, records in msg.items():
            for record in records:
                comment = record.value
                if not comment or not isinstance(comment, dict):
                    continue
                text = comment.get("body", "").strip()
                if text:
                    buffer.append(text)

        if len(buffer) >= BATCH_SIZE:
            try:
                vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
                X = vectorizer.fit_transform(buffer)

                kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
                labels = kmeans.fit_predict(X)

                topics = {}
                for i, label in enumerate(labels):
                    topics.setdefault(int(label), []).append(buffer[i])

                output = {
                    "batch_size": len(buffer),
                    "clusters": [
                        {"topic_id": int(k), "examples": v[:3]} for k, v in topics.items()
                    ],
                    "timestamp": time.time()
                }

                producer.send("processed_insights", value=output)
                print("Produced to processed_insights:", output)

            except Exception as e:
                print("Error in clustering:", e)

            buffer = []

    except KeyboardInterrupt:
        print("Shutting down consumer...")
        break

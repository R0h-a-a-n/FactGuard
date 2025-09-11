from kafka import KafkaConsumer
import json

def safe_deserialize(v):
    try:
        return json.loads(v.decode("utf-8"))
    except Exception:
        return None

consumer = KafkaConsumer(
    "processed_insights",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="latest",
    value_deserializer=safe_deserialize,
    enable_auto_commit=True,
    group_id="insights-reader"
)

print("Listening for processed insights..")

try:
    for msg in consumer:
        data = msg.value
        if not data:
            continue
        print("\n--New Batch---")
        print(f"Batch size: {data['batch_size']}")
        print(f"Timestamp: {data['timestamp']}")
        for cluster in data["clusters"]:
            print(f"Topic {cluster['topic_id']}:")
            for example in cluster["examples"]:
                print(f"   - {example[:120]}...") 
except KeyboardInterrupt:
    print("Shutting down insights consumer..")

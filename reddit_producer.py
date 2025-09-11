import praw
from kafka import KafkaProducer
import json
import time
import os

reddit = praw.Reddit(
    client_id = os.getenv("REDDIT_CLIENT_ID"),
    client_secret = os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent = os.getenv("REDDIT_USER_AGENT")
)

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

subreddit = reddit.subreddit("AskReddit")

print("Streaming comments from r/worldnews...")

while True:
    try:
        for comment in subreddit.stream.comments(skip_existing=True):
            data = {
                "id": comment.id,
                "body": comment.body,
                "created_utc": comment.created_utc,
                "author": str(comment.author),
            }
            producer.send("raw_comments_stream", value=data)
            print("Produced:", data)
    except Exception as e:
        print("Error:", e)
        time.sleep(5)

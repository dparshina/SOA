import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from confluent_kafka import Producer
from dotenv import load_dotenv, dotenv_values

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

class KafkaProducer:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'social_network_producer'
        })
        
        self.POST_VIEWED_TOPIC = "post_viewed"
        self.POST_LIKED_TOPIC = "post_liked"
        self.POST_COMMENTED_TOPIC = "post_commented"
        self.USER_REGISTERED_TOPIC = "user_registered"

    def _delivery_report(self, err, msg):
        if err:
            print(f'Отправка сообщения нарушена: {err}')
        else:
            print(f'Сообщение отправлено: {msg.topic()}')

    def _serialize(self, data: Dict) -> bytes:
        return json.dumps(data, default=self._datetime_serializer).encode('utf-8')

    def _datetime_serializer(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"Type {type(o)} not serializable")

    def send_event(self, topic: str, data: Dict):
        self.producer.produce(
            topic=topic,
            value=self._serialize(data),
            callback=self._delivery_report
        )
        self.producer.flush()

    def send_post_viewed_event(self, post_id: int, user_id: int):
        self.send_event(self.POST_VIEWED_TOPIC, data={
            "event_type": "post_viewed",
            "timestamp": datetime.utcnow(),
            "post_id": post_id,
            "user_id": user_id
        })

    def send_post_liked_event(self, post_id: int, user_id: int):
        self.send_event(self.POST_LIKED_TOPIC, data={
            "event_type": "post_liked",
            "timestamp": datetime.utcnow(),
            "post_id": post_id,
            "user_id": user_id
        })

    def send_post_commented_event(self, post_id: int, user_id: int, text: str):
        self.send_event(self.POST_COMMENTED_TOPIC, data={
            "event_type": "post_commented",
            "timestamp": datetime.utcnow(),
            "post_id": post_id,
            "user_id": user_id,
            "text": text
        })
    def send_user_registered_event(self, user_id: int, registered_at: datetime):
        self.send_event(self.USER_REGISTERED_TOPIC, data={
            "event_type": "user_registered",
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "registrated_at": registered_at
        })
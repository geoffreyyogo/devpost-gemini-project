import pika
import json
import logging
import time
import threading
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)

class RabbitMQService:
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self._is_connecting = False
        self._lock = threading.Lock()

    def connect(self):
        """Establish connection to RabbitMQ"""
        if self._connection and self._connection.is_open:
            return

        with self._lock:
            if self._is_connecting:
                return
            self._is_connecting = True
            
        try:
            logger.info(f"Connecting to RabbitMQ at {self.amqp_url}")
            params = pika.URLParameters(self.amqp_url)
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()
            
            # Declare common queues
            self._channel.queue_declare(queue='sms_queue', durable=True)
            self._channel.queue_declare(queue='email_queue', durable=True)
            self._channel.queue_declare(queue='ai_processing_queue', durable=True)
            
            logger.info("✓ RabbitMQ connected")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self._connection = None
            self._channel = None
        finally:
            with self._lock:
                self._is_connecting = False

    def ensure_connection(self):
        """Check connection and reconnect if needed"""
        if not self._connection or not self._connection.is_open:
            self.connect()

    def publish_message(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a queue"""
        try:
            self.ensure_connection()
            if not self._channel:
                return False

            self._channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json'
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish to {queue_name}: {e}")
            # Try once to reconnect
            try:
                self._connection = None
                self.connect()
                if self._channel:
                    self._channel.basic_publish(
                        exchange='',
                        routing_key=queue_name,
                        body=json.dumps(message),
                        properties=pika.BasicProperties(delivery_mode=2)
                    )
                    return True
            except Exception as retry_e:
                logger.error(f"Retry publish failed: {retry_e}")
            return False

    def close(self):
        """Close connection cleanly"""
        if self._connection and self._connection.is_open:
            self._connection.close()

# Singleton instance placeholder
rabbitmq_service: Optional[RabbitMQService] = None

# server/worker.py
import os
import json
import logging
import time
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("worker")

# Load env vars
load_dotenv()

from rabbitmq_service import RabbitMQService
from africastalking_service import AfricasTalkingService
# We need a dummy DB service or similar if AfricasTalkingService requires it
# Looking at main.py imports: `from africastalking_service import AfricasTalkingService`
# It usually takes `db_service`.
# Let's check `africastalking_service.py` constructor.

# For now, I'll assume I can instantiate it or extract the sending logic.
# I'll modify the import later if needed.

def process_sms(ch, method, properties, body):
    """Callback for processing SMS queue items"""
    try:
        data = json.loads(body)
        to_phone = data.get('to')
        message = data.get('message')
        
        if not to_phone or not message:
            logger.warning("Invalid SMS payload")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        logger.info(f"Processing SMS for {to_phone}")
        
        # Here we need the sms_service instance.
        # Since this is a callback, we'll use a global or pass it in closure.
        # Ideally, we instantiate services outside.
        
        # ACTUALLY SEND SMS
        # sms_service.send_sms(to_phone, message)
        # We need to make sure we have access to sms_service here.
        
        # For this implementation, I will rely on the global `sms_service` initialized in main block.
        result = sms_service.send_sms(to_phone, message)
        
        if result.get('success'):
            logger.info(f"✓ SMS sent to {to_phone}")
        else:
            logger.error(f"✗ SMS failed to {to_phone}: {result.get('error')}")
            
        ch.basic_ack(delivery_tag=method.delivery_tag)
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Reject and requeue if transient error? Or just ack to avoid loop?
        # For now, ack to clear bad messages
        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":
    logger.info("Starting Worker...")
    
    # 1. Init Database (for AT service dependency)
    from database.connection import DBService
    db_service = DBService() # Might need init params
    
    # 2. Init AfricasTalking Service
    # Note: DB service might not be strictly needed for SENDING, only for logging?
    # Checking if `sms_service = AfricasTalkingService(db_service=db_service)`
    sms_service = AfricasTalkingService(db_service=db_service)
    
    # 3. Init RabbitMQ
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    mq = RabbitMQService(RABBITMQ_URL)
    mq.connect()
    
    if mq._connection:
        logger.info("Worker connected to RabbitMQ. Waiting for messages...")
        
        # Set QoS to 1 to process one by one
        mq._channel.basic_qos(prefetch_count=1)
        
        # Start consuming
        mq._channel.basic_consume(
            queue='sms_queue', 
            on_message_callback=process_sms
        )
        
        try:
            mq._channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping worker...")
            mq.close()
    else:
        logger.error("Could not connect to RabbitMQ from worker.")

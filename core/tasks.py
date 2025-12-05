from celery import shared_task
import time
import random
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=3)
def send_transfer_notification(self, tx_id, email):
    logger.info(f"Starting notification task for TX {tx_id} to {email}")
    
    try:
        # Fake 
        time.sleep(5)
        
        # Fake network fail connection (for retry)
        if random.choice([True, False]): 
            raise ConnectionError("Simulated network failure")
            
        logger.info(f"Notification sent for TX {tx_id} to {email}")
        return "Sent"
        
    except ConnectionError as exc:
        logger.warning(f"Network error for TX {tx_id}. Retrying... ({self.request.retries + 1}/3)")
        raise self.retry(exc=exc)
    except Exception as exc:
        logger.error(f"Critical error sending notification for TX {tx_id}: {exc}")
        raise 
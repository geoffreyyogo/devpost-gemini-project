"""
Automated Data Scheduler for Kenya Satellite Data
Fetches and updates data periodically
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from kenya_data_fetcher import KenyaDataFetcher
from train_model import BloomPredictor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataScheduler:
    """Schedule periodic data fetches and model retraining"""
    
    def __init__(self):
        """Initialize the scheduler"""
        self.fetcher = KenyaDataFetcher()
        self.predictor = BloomPredictor()
        logger.info("Data Scheduler initialized")
    
    def fetch_all_counties(self):
        """Fetch data for all counties"""
        try:
            logger.info("="*60)
            logger.info("Starting scheduled data fetch for all counties")
            logger.info("="*60)
            
            start_time = datetime.now()
            
            # Fetch all county data
            data = self.fetcher.fetch_all_counties_data(priority_agricultural=True)
            
            elapsed = datetime.now() - start_time
            
            summary = self.fetcher.get_data_summary()
            
            logger.info("="*60)
            logger.info("DATA FETCH COMPLETED")
            logger.info(f"Time taken: {elapsed}")
            logger.info(f"Counties fetched: {summary['total_counties']}")
            logger.info(f"Real satellite data: {summary['counties_with_real_data']}/{summary['total_counties']}")
            logger.info(f"Avg bloom probability: {summary['avg_bloom_probability']:.1f}%")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error in scheduled data fetch: {e}")
    
    def fetch_priority_counties(self):
        """Fetch data for agricultural priority counties only"""
        try:
            logger.info("Starting priority counties data fetch")
            
            from kenya_counties_config import AGRICULTURAL_COUNTIES
            
            for county_id in AGRICULTURAL_COUNTIES[:10]:  # Top 10 priority
                self.fetcher.fetch_county_data(county_id)
            
            logger.info("Priority counties fetch completed")
            
        except Exception as e:
            logger.error(f"Error in priority fetch: {e}")
    
    def retrain_model(self):
        """Retrain the bloom prediction model"""
        try:
            logger.info("="*60)
            logger.info("Starting scheduled model retraining")
            logger.info("="*60)
            
            result = self.predictor.train_model(retrain=True)
            
            if 'error' not in result:
                logger.info("MODEL RETRAINING COMPLETED")
                logger.info(f"Accuracy: {result.get('accuracy', 'N/A')}")
                logger.info(f"F1 Score: {result.get('f1_score', 'N/A')}")
            else:
                logger.error(f"Model retraining failed: {result['error']}")
            
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error in model retraining: {e}")
    
    def run_scheduled_tasks(self):
        """Set up and run scheduled tasks"""
        logger.info("Setting up scheduled tasks...")
        
        # Schedule tasks
        # - Full data fetch: Every 6 hours
        schedule.every(6).hours.do(self.fetch_all_counties)
        
        # - Priority counties: Every 1 hour
        schedule.every(1).hours.do(self.fetch_priority_counties)
        
        # - Model retraining: Every Monday at 2 AM
        schedule.every().monday.at("02:00").do(self.retrain_model)
        
        # - Model retraining: Also weekly (every 7 days)
        schedule.every(7).days.do(self.retrain_model)
        
        logger.info("Scheduled tasks:")
        logger.info("  - Full data fetch: Every 6 hours")
        logger.info("  - Priority counties: Every 1 hour")
        logger.info("  - Model retraining: Every Monday at 2 AM and every 7 days")
        logger.info("")
        logger.info("Running initial data fetch...")
        
        # Run initial fetch immediately
        self.fetch_all_counties()
        
        logger.info("\n" + "="*60)
        logger.info("SCHEDULER IS NOW RUNNING")
        logger.info("Press Ctrl+C to stop")
        logger.info("="*60 + "\n")
        
        # Run scheduler loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("\nScheduler stopped by user")
    
    def run_once(self, task: str = 'all'):
        """Run a task once without scheduling"""
        if task == 'all':
            self.fetch_all_counties()
        elif task == 'priority':
            self.fetch_priority_counties()
        elif task == 'retrain':
            self.retrain_model()
        else:
            logger.error(f"Unknown task: {task}")


# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Schedule automated data fetching')
    parser.add_argument('--run-scheduler', action='store_true', help='Run continuous scheduler')
    parser.add_argument('--run-once', type=str, choices=['all', 'priority', 'retrain'], 
                       help='Run a single task once')
    
    args = parser.parse_args()
    
    scheduler = DataScheduler()
    
    if args.run_scheduler:
        scheduler.run_scheduled_tasks()
    elif args.run_once:
        scheduler.run_once(args.run_once)
    else:
        print("Usage:")
        print("  python data_scheduler.py --run-scheduler          # Run continuous scheduler")
        print("  python data_scheduler.py --run-once all           # Fetch all counties once")
        print("  python data_scheduler.py --run-once priority      # Fetch priority counties once")
        print("  python data_scheduler.py --run-once retrain       # Retrain model once")


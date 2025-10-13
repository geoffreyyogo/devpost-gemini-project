"""
Automated Scheduler Service for BloomWatch Kenya
Handles periodic data fetching, archiving, and maintenance tasks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import shutil
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class SchedulerService:
    """
    Manages automated background tasks:
    - Weekly data fetching from NASA satellites
    - Historical data archiving
    - Database cleanup
    - Alert generation
    """
    
    def __init__(self, data_loader, mongo_service, alert_service, bloom_predictor=None):
        self.data_loader = data_loader
        self.mongo = mongo_service
        self.alerts = alert_service
        self.bloom_predictor = bloom_predictor
        self.is_running = False
        self.tasks = []
        
        # Directories
        self.base_dir = Path(__file__).parent.parent / 'data' / 'exports'
        self.live_dir = self.base_dir / 'live'
        self.historical_dir = self.base_dir / 'historical'
        
        # Ensure directories exist
        self.live_dir.mkdir(parents=True, exist_ok=True)
        self.historical_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("✓ Scheduler Service initialized")
    
    async def start(self):
        """Start all scheduled tasks"""
        self.is_running = True
        logger.info("🕐 Starting scheduler service...")
        
        # Schedule tasks
        self.tasks = [
            asyncio.create_task(self._weekly_data_fetch()),
            asyncio.create_task(self._daily_archive_old_data()),
            asyncio.create_task(self._daily_cleanup()),
            asyncio.create_task(self._weekly_ml_retrain()),
        ]
        
        logger.info(f"✓ {len(self.tasks)} scheduled tasks started")
    
    async def stop(self):
        """Stop all scheduled tasks"""
        self.is_running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Scheduler service stopped")
    
    async def _weekly_data_fetch(self):
        """
        Fetch fresh satellite data every week
        Runs every Sunday at 2 AM
        """
        while self.is_running:
            try:
                now = datetime.now()
                
                # Calculate next Sunday at 2 AM
                days_until_sunday = (6 - now.weekday()) % 7
                if days_until_sunday == 0 and now.hour >= 2:
                    days_until_sunday = 7
                
                next_run = (now + timedelta(days=days_until_sunday)).replace(
                    hour=2, minute=0, second=0, microsecond=0
                )
                
                # Wait until next run
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"📅 Next weekly data fetch scheduled for: {next_run} ({wait_seconds/3600:.1f} hours)")
                
                await asyncio.sleep(wait_seconds)
                
                # Perform weekly data fetch
                logger.info("🚀 Starting weekly NASA data fetch for all counties...")
                
                try:
                    # Import here to avoid circular dependencies
                    from kenya_data_fetcher import fetch_all_counties_data
                    
                    counties_data = await asyncio.to_thread(fetch_all_counties_data)
                    
                    logger.info(f"✅ Weekly fetch complete: {len(counties_data)} counties updated")
                    
                    # Archive previous week's live data to historical
                    await self._archive_live_to_historical()
                    
                except Exception as e:
                    logger.error(f"Weekly fetch failed: {e}", exc_info=True)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in weekly fetch scheduler: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
    
    async def _daily_archive_old_data(self):
        """
        Archive old live data to historical directory
        Runs daily at 3 AM
        """
        while self.is_running:
            try:
                now = datetime.now()
                
                # Calculate next 3 AM
                next_run = (now + timedelta(days=1)).replace(
                    hour=3, minute=0, second=0, microsecond=0
                )
                if now.hour < 3:
                    next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"📦 Next archive scheduled for: {next_run}")
                
                await asyncio.sleep(wait_seconds)
                
                # Archive data older than 7 days
                await self._archive_live_to_historical(days_old=7)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in archive scheduler: {e}")
                await asyncio.sleep(3600)
    
    async def _daily_cleanup(self):
        """
        Clean up expired sessions and temporary files
        Runs daily at 4 AM
        NOTE: Historical data is PRESERVED for ML training (not deleted)
        """
        while self.is_running:
            try:
                now = datetime.now()
                
                # Calculate next 4 AM
                next_run = (now + timedelta(days=1)).replace(
                    hour=4, minute=0, second=0, microsecond=0
                )
                if now.hour < 4:
                    next_run = now.replace(hour=4, minute=0, second=0, microsecond=0)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"🧹 Next cleanup scheduled for: {next_run}")
                
                await asyncio.sleep(wait_seconds)
                
                # Clean up expired sessions (older than 30 days)
                try:
                    cutoff = datetime.now() - timedelta(days=30)
                    result = self.mongo.db.sessions.delete_many({
                        "created_at": {"$lt": cutoff}
                    })
                    logger.info(f"Cleaned up {result.deleted_count} expired sessions")
                except Exception as e:
                    logger.error(f"Session cleanup failed: {e}")
                
                # Clean up VERY old historical data (older than 2 years for storage management)
                # Keep 2 years of data for robust ML training
                try:
                    await self._cleanup_old_historical_data(months_old=24)
                except Exception as e:
                    logger.error(f"Historical data cleanup failed: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup scheduler: {e}")
                await asyncio.sleep(3600)
    
    async def _archive_live_to_historical(self, days_old: int = 7):
        """
        Move old live data files to historical directory
        
        Args:
            days_old: Archive files older than this many days
        """
        try:
            logger.info(f"📦 Archiving live data older than {days_old} days...")
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            archived_count = 0
            
            # Get all CSV files in live directory
            for file_path in self.live_dir.glob('*.csv'):
                # Get file modification time
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    # Create year/month subdirectory in historical
                    year_month = file_mtime.strftime('%Y-%m')
                    archive_subdir = self.historical_dir / year_month
                    archive_subdir.mkdir(parents=True, exist_ok=True)
                    
                    # Move file to historical
                    dest_path = archive_subdir / file_path.name
                    shutil.move(str(file_path), str(dest_path))
                    archived_count += 1
                    logger.info(f"Archived: {file_path.name} → historical/{year_month}/")
            
            logger.info(f"✅ Archived {archived_count} files to historical directory")
            
            # Also save a metadata file
            if archived_count > 0:
                metadata_file = self.historical_dir / f"archive_log_{datetime.now().strftime('%Y%m%d')}.txt"
                with open(metadata_file, 'a') as f:
                    f.write(f"{datetime.now()}: Archived {archived_count} files\n")
            
        except Exception as e:
            logger.error(f"Error archiving data: {e}", exc_info=True)
    
    async def _cleanup_old_historical_data(self, months_old: int = 6):
        """Delete historical data older than specified months"""
        try:
            cutoff_date = datetime.now() - timedelta(days=months_old * 30)
            deleted_count = 0
            
            for file_path in self.historical_dir.rglob('*.csv'):
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    file_path.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🧹 Deleted {deleted_count} old historical files (>{months_old} months)")
            
        except Exception as e:
            logger.error(f"Error cleaning up historical data: {e}")
    
    async def _weekly_ml_retrain(self):
        """
        Retrain ML model weekly with fresh data
        Runs every Monday at 5 AM (after data fetch and archiving)
        """
        while self.is_running:
            try:
                now = datetime.now()
                
                # Calculate next Monday at 5 AM
                days_until_monday = (7 - now.weekday()) % 7
                if days_until_monday == 0 and now.hour >= 5:
                    days_until_monday = 7
                
                next_run = (now + timedelta(days=days_until_monday)).replace(
                    hour=5, minute=0, second=0, microsecond=0
                )
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"🤖 Next ML retraining scheduled for: {next_run}")
                
                await asyncio.sleep(wait_seconds)
                
                # Retrain model with latest data (live + historical)
                if self.bloom_predictor:
                    logger.info("🤖 Starting ML model retraining with live + historical data...")
                    
                    try:
                        result = await asyncio.to_thread(
                            self.bloom_predictor.train_model,
                            include_weather=True,
                            optimize_hyperparameters=False
                        )
                        
                        if 'error' not in result:
                            logger.info(f"✅ ML model retrained successfully!")
                            logger.info(f"   Accuracy: {result.get('accuracy', 'N/A')}")
                            logger.info(f"   F1 Score: {result.get('f1_score', 'N/A')}")
                            logger.info(f"   Training samples: {result.get('n_samples', 'N/A')}")
                        else:
                            logger.error(f"ML retraining failed: {result['error']}")
                            
                    except Exception as e:
                        logger.error(f"ML retraining error: {e}", exc_info=True)
                else:
                    logger.warning("ML predictor not available, skipping retraining")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ML retrain scheduler: {e}")
                await asyncio.sleep(3600)
    
    async def trigger_immediate_fetch(self):
        """Manually trigger data fetch (for admin/testing)"""
        logger.info("🚀 Manual data fetch triggered...")
        try:
            from kenya_data_fetcher import fetch_all_counties_data
            counties_data = await asyncio.to_thread(fetch_all_counties_data)
            logger.info(f"✅ Manual fetch complete: {len(counties_data)} counties")
            return {"success": True, "counties": len(counties_data)}
        except Exception as e:
            logger.error(f"Manual fetch failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def trigger_immediate_retrain(self):
        """Manually trigger ML model retraining"""
        logger.info("🤖 Manual ML retraining triggered...")
        try:
            if not self.bloom_predictor:
                return {"success": False, "error": "ML predictor not available"}
            
            result = await asyncio.to_thread(
                self.bloom_predictor.train_model,
                include_weather=True,
                optimize_hyperparameters=False
            )
            
            if 'error' not in result:
                logger.info(f"✅ Manual retrain complete: Accuracy {result.get('accuracy', 'N/A')}")
                return {
                    "success": True,
                    "accuracy": result.get('accuracy'),
                    "f1_score": result.get('f1_score'),
                    "n_samples": result.get('n_samples')
                }
            else:
                return {"success": False, "error": result['error']}
        except Exception as e:
            logger.error(f"Manual retrain failed: {e}")
            return {"success": False, "error": str(e)}


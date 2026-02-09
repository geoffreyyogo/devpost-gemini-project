"""
Automated Scheduler Service for Smart Shamba
Handles periodic data fetching, archiving, maintenance, and ML retraining.

Uses asyncio tasks (Celery-ready design — swap asyncio.sleep with Celery beat
when RabbitMQ is available).
"""

import asyncio
import logging
from datetime import datetime, timedelta, date as date_type
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Manages automated background tasks:
    - Weekly data fetching from NASA satellites (all counties + sub-counties)
    - Historical data archiving
    - Database cleanup (expired sessions via PostgreSQL)
    - Weekly ML model retraining
    """

    def __init__(self, data_loader, db_service, alert_service, bloom_predictor=None):
        """
        Args:
            data_loader: StreamlitDataLoader (legacy — kept for compat)
            db_service: PostgresService instance
            alert_service: SmartAlertService instance
            bloom_predictor: BloomPredictor instance (or None)
        """
        self.data_loader = data_loader
        self.db = db_service
        self.alerts = alert_service
        self.bloom_predictor = bloom_predictor
        self.is_running = False
        self.tasks = []
        self._fetcher = None  # lazy-init KenyaDataFetcher

        logger.info("✓ Scheduler Service initialized")

    # -------------------------------------------------------------- #
    # Lazy accessor for fetcher (avoids import at module level)
    # -------------------------------------------------------------- #

    def _get_fetcher(self):
        """Lazily import and create KenyaDataFetcher to avoid circular imports."""
        if self._fetcher is None:
            from kenya_data_fetcher import KenyaDataFetcher
            self._fetcher = KenyaDataFetcher(db_service=self.db)
        return self._fetcher

    # -------------------------------------------------------------- #
    # Start / Stop
    # -------------------------------------------------------------- #

    async def start(self):
        """Start all scheduled tasks."""
        self.is_running = True
        logger.info("🕐 Starting scheduler service...")

        self.tasks = [
            asyncio.create_task(self._weekly_data_fetch()),
            asyncio.create_task(self._daily_cleanup()),
            asyncio.create_task(self._periodic_smart_alerts()),
        ]

        logger.info(f"✓ {len(self.tasks)} scheduled tasks started")

    async def stop(self):
        """Stop all scheduled tasks."""
        self.is_running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Scheduler service stopped")

    # -------------------------------------------------------------- #
    # 1. Weekly satellite data fetch  (Sunday 2 AM)
    # -------------------------------------------------------------- #

    async def _weekly_data_fetch(self):
        """Fetch fresh satellite data every Sunday at 2 AM, then retrain."""
        while self.is_running:
            try:
                wait = self._seconds_until(weekday=6, hour=2)  # Sunday
                logger.info(
                    f"📅 Next weekly data fetch in {wait / 3600:.1f} hours "
                    f"({self._next_run_str(weekday=6, hour=2)})"
                )
                await asyncio.sleep(wait)

                logger.info("🚀 Starting weekly satellite data fetch for all counties...")
                fetch_ok = False
                try:
                    fetcher = self._get_fetcher()
                    counties_data = await asyncio.to_thread(
                        fetcher.fetch_all_counties_data,
                        priority_agricultural=True,
                    )
                    logger.info(
                        f"✅ Weekly county fetch complete: {len(counties_data)} counties updated"
                    )
                    fetch_ok = True

                except Exception as e:
                    logger.error(f"Weekly county fetch failed: {e}", exc_info=True)

                # Also fetch sub-county data for priority agricultural counties
                PRIORITY_SUB_COUNTY_COUNTIES = [
                    'kisumu', 'siaya', 'homa_bay', 'migori', 'busia',
                    'kakamega', 'bungoma', 'trans_nzoia', 'uasin_gishu',
                    'nandi', 'kericho', 'bomet', 'nakuru', 'nyandarua',
                    'nyeri', 'kirinyaga', 'muranga', 'kiambu', 'meru',
                    'embu', 'tharaka_nithi', 'machakos', 'makueni',
                ]
                sc_fetched = 0
                try:
                    fetcher = self._get_fetcher()
                    for county_id in PRIORITY_SUB_COUNTY_COUNTIES:
                        try:
                            result = await asyncio.to_thread(
                                fetcher.fetch_county_with_sub_counties, county_id
                            )
                            sc_count = result.get('sub_counties_fetched', 0) if isinstance(result, dict) else 0
                            sc_fetched += sc_count
                        except Exception as e:
                            logger.warning(f"Sub-county fetch failed for {county_id}: {e}")
                    logger.info(f"✅ Weekly sub-county fetch complete: {sc_fetched} sub-counties across {len(PRIORITY_SUB_COUNTY_COUNTIES)} counties")
                except Exception as e:
                    logger.error(f"Weekly sub-county fetch failed: {e}", exc_info=True)

                # Chain: retrain on old + new data after successful fetch
                if fetch_ok:
                    await self._retrain_after_fetch()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in weekly fetch scheduler: {e}")
                await asyncio.sleep(3600)

    # -------------------------------------------------------------- #
    # 2. Daily cleanup (4 AM) — PostgreSQL session cleanup
    # -------------------------------------------------------------- #

    async def _daily_cleanup(self):
        """
        Clean up expired sessions and old temporary data (daily at 4 AM).
        """
        while self.is_running:
            try:
                wait = self._seconds_until_today_or_tomorrow(hour=4)
                logger.info(f"🧹 Next cleanup scheduled in {wait / 3600:.1f} hours")
                await asyncio.sleep(wait)

                # 1) Clean expired user sessions via PostgreSQL
                try:
                    deleted = await asyncio.to_thread(
                        self.db.cleanup_expired_sessions
                    )
                    logger.info(f"Cleaned up {deleted} expired user sessions")
                except Exception as e:
                    logger.error(f"Session cleanup failed: {e}")

                # 2) Clean expired USSD sessions (older than 24 hours)
                try:
                    deleted_ussd = await asyncio.to_thread(
                        self._cleanup_expired_ussd_sessions
                    )
                    logger.info(f"Cleaned up {deleted_ussd} expired USSD sessions")
                except Exception as e:
                    logger.error(f"USSD session cleanup failed: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup scheduler: {e}")
                await asyncio.sleep(3600)

    # -------------------------------------------------------------- #
    # 3. Auto-retrain after data fetch (chained, not standalone)
    # -------------------------------------------------------------- #

    async def _retrain_after_fetch(self):
        """
        Retrain ML model immediately after a successful data fetch.
        Uses ALL historical data (old + new) from PostgreSQL.
        Called automatically by _weekly_data_fetch and trigger_immediate_fetch.
        """
        if not self.bloom_predictor:
            logger.warning("ML predictor not available, skipping post-fetch retraining")
            return

        logger.info("🤖 Starting ML model retraining (chained after data fetch)...")
        try:
            result = await asyncio.to_thread(
                self.bloom_predictor.train_model,
                include_weather=True,
                optimize_hyperparameters=False,
            )
            if "error" not in result:
                logger.info("✅ Post-fetch ML retrain complete!")
                logger.info(f"   Accuracy: {result.get('accuracy', 'N/A')}")
                logger.info(f"   F1 Score: {result.get('f1_score', 'N/A')}")
                logger.info(
                    f"   Training samples: {result.get('n_samples', 'N/A')}"
                )
            else:
                logger.error(f"Post-fetch ML retraining failed: {result['error']}")
        except Exception as e:
            logger.error(f"Post-fetch ML retraining error: {e}", exc_info=True)

    # -------------------------------------------------------------- #
    # 4. Periodic smart alert scan (every 6 hours)
    # -------------------------------------------------------------- #

    async def _periodic_smart_alerts(self):
        """
        Scan all farmers every 6 hours for extreme weather events,
        IoT sensor anomalies, and satellite-data alerts.

        Uses SmartAlertService.run_scheduled_smart_alerts() which:
          - Fetches weather forecast for each farmer's location
          - Pulls latest IoT sensor readings from their farms
          - Pulls satellite data for their county
          - Detects extreme events and auto-sends alerts
        """
        while self.is_running:
            try:
                wait = self._seconds_until_today_or_tomorrow(hour=6)
                # Run at 6AM, 12PM, 6PM, 12AM — every 6 hours
                wait = min(wait, 6 * 3600)
                logger.info(
                    f"🔔 Next smart alert scan in {wait / 3600:.1f} hours"
                )
                await asyncio.sleep(wait)

                logger.info("🔔 Starting periodic smart alert scan...")
                try:
                    result = await self.alerts.run_scheduled_smart_alerts()
                    logger.info(
                        f"✅ Alert scan complete: "
                        f"{result.get('farmers_scanned', 0)} farmers scanned, "
                        f"{result.get('extreme_alerts_sent', 0)} extreme alerts, "
                        f"{result.get('condition_alerts_sent', 0)} condition alerts"
                    )
                except Exception as e:
                    logger.error(f"Periodic alert scan failed: {e}", exc_info=True)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in smart alert scheduler: {e}")
                await asyncio.sleep(3600)

    # -------------------------------------------------------------- #
    # Manual trigger helpers (for admin endpoints)
    # -------------------------------------------------------------- #

    async def trigger_immediate_fetch(
        self,
        scope: str = "country",
        county_id: str = None,
        region: str = None,
        sub_county_id: str = None,
        retrain: bool = True,
    ) -> Dict:
        """
        Manually trigger data fetch at any granularity.

        Args:
            scope: 'country' | 'region' | 'county' | 'sub_county'
            county_id: required when scope is 'county' or 'sub_county'
            region: required when scope is 'region'
            sub_county_id: required when scope is 'sub_county'
            retrain: If True, chain ML retrain after fetch (default True)
        """
        logger.info(f"🚀 Manual data fetch triggered (scope={scope})...")
        try:
            fetcher = self._get_fetcher()

            if scope == "sub_county" and county_id and sub_county_id:
                data = await asyncio.to_thread(
                    fetcher.fetch_sub_county_data, county_id, sub_county_id
                )
                result = {"success": "error" not in data, "scope": "sub_county", "data": data}

            elif scope == "county" and county_id:
                data = await asyncio.to_thread(fetcher.fetch_county_data, county_id)
                result = {"success": "error" not in data, "scope": "county", "data": data}

            elif scope == "region" and region:
                data = await asyncio.to_thread(fetcher.fetch_region_data, region)
                result = {"success": True, "scope": "region", "counties": len(data)}

            else:  # country
                data = await asyncio.to_thread(fetcher.fetch_all_counties_data)
                result = {"success": True, "scope": "country", "counties": len(data)}

            # Chain retrain on old + new data if fetch succeeded
            if retrain and result.get("success"):
                await self._retrain_after_fetch()
                result["retrained"] = True

            return result

        except Exception as e:
            logger.error(f"Manual fetch failed: {e}")
            return {"success": False, "error": str(e)}

    async def trigger_immediate_retrain(self) -> Dict:
        """Manually trigger ML model retraining."""
        logger.info("🤖 Manual ML retraining triggered...")
        try:
            if not self.bloom_predictor:
                return {"success": False, "error": "ML predictor not available"}

            result = await asyncio.to_thread(
                self.bloom_predictor.train_model,
                include_weather=True,
                optimize_hyperparameters=False,
            )

            if "error" not in result:
                logger.info(
                    f"✅ Manual retrain complete: Accuracy {result.get('accuracy', 'N/A')}"
                )
                return {
                    "success": True,
                    "accuracy": result.get("accuracy"),
                    "f1_score": result.get("f1_score"),
                    "n_samples": result.get("n_samples"),
                }
            return {"success": False, "error": result["error"]}
        except Exception as e:
            logger.error(f"Manual retrain failed: {e}")
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------- #
    # Internal helpers
    # -------------------------------------------------------------- #

    def _cleanup_expired_ussd_sessions(self) -> int:
        """Delete USSD sessions older than 24 hours via PostgreSQL."""
        if not self.db or not self.db._connected:
            return 0
        try:
            from sqlmodel import Session as DBSession, delete
            from database.connection import engine
            from database.models import USSDSession

            cutoff = datetime.utcnow() - timedelta(hours=24)
            with DBSession(engine) as session:
                result = session.exec(
                    delete(USSDSession).where(USSDSession.created_at < cutoff)
                )
                session.commit()
                return result.rowcount or 0  # type: ignore[union-attr]
        except Exception as e:
            logger.error(f"USSD session cleanup error: {e}")
            return 0

    # -------------------------------------------------------------- #
    # Time calculation helpers
    # -------------------------------------------------------------- #

    @staticmethod
    def _seconds_until(weekday: int, hour: int) -> float:
        """Seconds until next occurrence of *weekday* at *hour*:00."""
        now = datetime.now()
        days_ahead = (weekday - now.weekday()) % 7
        if days_ahead == 0 and now.hour >= hour:
            days_ahead = 7
        target = (now + timedelta(days=days_ahead)).replace(
            hour=hour, minute=0, second=0, microsecond=0
        )
        return max((target - now).total_seconds(), 0)

    @staticmethod
    def _seconds_until_today_or_tomorrow(hour: int) -> float:
        """Seconds until next *hour*:00 today or tomorrow."""
        now = datetime.now()
        target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        return max((target - now).total_seconds(), 0)

    @staticmethod
    def _next_run_str(weekday: int, hour: int) -> str:
        now = datetime.now()
        days_ahead = (weekday - now.weekday()) % 7
        if days_ahead == 0 and now.hour >= hour:
            days_ahead = 7
        target = (now + timedelta(days=days_ahead)).replace(
            hour=hour, minute=0, second=0, microsecond=0
        )
        return target.strftime("%A %Y-%m-%d %H:%M")


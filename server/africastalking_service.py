"""
Africa's Talking SMS & USSD Service for Smart Shamba Platform

Provides SMS sending via Africa's Talking SDK and USSD callback handling.

Environment variables:
    AT_USERNAME      – Africa's Talking username (sandbox or production)
    AT_API_KEY       – Africa's Talking API key
    AT_SENDER_ID     – Registered shortcode / sender ID (optional)
    AT_ENVIRONMENT   – 'sandbox' or 'production' (default: sandbox)
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Try to import Africa's Talking SDK
try:
    import africastalking
    AT_SDK_AVAILABLE = True
except ImportError:
    AT_SDK_AVAILABLE = False
    logger.warning(
        "africastalking package not installed.  "
        "Install with: pip install africastalking"
    )


class AfricasTalkingService:
    """Africa's Talking SMS + USSD service."""

    def __init__(self, db_service=None):
        self.username = os.getenv("AT_USERNAME", "sandbox")
        self.api_key = os.getenv("AT_API_KEY", "")
        self.sender_id = os.getenv("AT_SENDER_ID", "")  # shortcode
        self.environment = os.getenv("AT_ENVIRONMENT", "sandbox")

        self.sms_client = None
        self._demo_mode = True

        if AT_SDK_AVAILABLE and self.api_key:
            try:
                africastalking.initialize(self.username, self.api_key)
                self.sms_client = africastalking.SMS
                self._demo_mode = False
                logger.info(
                    f"✓ Africa's Talking SMS service initialised "
                    f"(user={self.username}, env={self.environment})"
                )
            except Exception as e:
                logger.warning(f"Africa's Talking init failed: {e}")
        else:
            if not AT_SDK_AVAILABLE:
                logger.warning("africastalking SDK not installed — running in demo mode")
            elif not self.api_key:
                logger.warning("AT_API_KEY not set — running in demo mode")

        # Optional DB service for logging
        self.db = db_service

    # ------------------------------------------------------------------ #
    # Phone number formatting
    # ------------------------------------------------------------------ #

    @staticmethod
    def format_phone(phone: str) -> str:
        """
        Normalise to international format WITH the + prefix,
        which is what Africa's Talking expects (e.g. +254712345678).
        """
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("+"):
            return phone
        if phone.startswith("0"):
            return "+254" + phone[1:]
        if phone.startswith("254"):
            return "+" + phone
        if len(phone) == 9:
            return "+254" + phone
        return "+" + phone

    # ------------------------------------------------------------------ #
    # Send SMS
    # ------------------------------------------------------------------ #

    def send_sms(self, phone: str, message: str) -> Dict:
        """
        Send a single SMS via Africa's Talking.

        Returns:
            {"success": bool, "message_id": str | None, ...}
        """
        phone = self.format_phone(phone)

        if self._demo_mode:
            logger.info(f"[DEMO] SMS → {phone}: {message[:80]}…")
            return {
                "success": True,
                "demo": True,
                "phone": phone,
                "message": "Demo mode — SMS not actually sent",
            }

        try:
            kwargs: Dict = {"message": message, "recipients": [phone]}
            if self.sender_id:
                kwargs["sender_id"] = self.sender_id

            response = self.sms_client.send(**kwargs)

            # AT returns: {"SMSMessageData": {"Recipients": [...]}}
            recipients = (
                response.get("SMSMessageData", {}).get("Recipients", [])
            )
            if recipients:
                first = recipients[0]
                status = first.get("status", "")
                msg_id = first.get("messageId", "")
                cost = first.get("cost", "")
                success = status in ("Success", "Sent")
                if success:
                    logger.info(f"✓ SMS sent to {phone} (cost={cost})")
                else:
                    logger.warning(f"SMS to {phone} status={status}")
                return {
                    "success": success,
                    "phone": phone,
                    "message_id": msg_id,
                    "cost": cost,
                    "status": status,
                }
            else:
                msg = response.get("SMSMessageData", {}).get("Message", "")
                logger.warning(f"AT SMS no recipients in response: {msg}")
                return {"success": False, "phone": phone, "error": msg}

        except Exception as e:
            logger.error(f"Error sending SMS to {phone}: {e}")
            return {"success": False, "phone": phone, "error": str(e)}

    # ------------------------------------------------------------------ #
    # Bulk SMS
    # ------------------------------------------------------------------ #

    def send_bulk_sms(self, recipients: List[Dict], message_template: str) -> Dict:
        """
        Send personalised SMS to multiple farmers.

        Each recipient dict should have: phone, name, crops (list), language.
        message_template can use {name} and {crop} placeholders.
        """
        results: Dict = {"sent": 0, "failed": 0, "details": []}

        for farmer in recipients:
            phone = farmer.get("phone", "")
            message = message_template.format(
                name=farmer.get("name", "Farmer"),
                crop=", ".join(farmer.get("crops", ["crop"])),
            )

            result = self.send_sms(phone, message)

            if result.get("success"):
                results["sent"] += 1
                if self.db:
                    self.db.log_alert(
                        str(farmer.get("_id", farmer.get("id", ""))),
                        {
                            "alert_type": "sms",
                            "message": message,
                            "channel": "sms",
                            "delivered": True,
                        },
                    )
            else:
                results["failed"] += 1

            results["details"].append(result)

        logger.info(
            f"✓ Bulk SMS: {results['sent']} sent, {results['failed']} failed"
        )
        return results

    # ------------------------------------------------------------------ #
    # Delivery report webhook handler
    # ------------------------------------------------------------------ #

    def handle_delivery_report(self, report_data: Dict) -> bool:
        """
        Handle incoming delivery report callback from Africa's Talking.
        """
        if self.db:
            return self.db.save_delivery_report(
                {
                    "messageId": report_data.get("id"),
                    "phoneNumber": report_data.get("phoneNumber"),
                    "status": report_data.get("status"),
                    "provider": "africastalking",
                }
            )
        return True


# ------------------------------------------------------------------ #
# Quick test
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    print("🌾 Smart Shamba — Africa's Talking SMS Test")
    print("=" * 60)

    svc = AfricasTalkingService()
    print(f"Demo mode: {svc._demo_mode}")

    # Test phone format
    tests = ["+254712345678", "0712345678", "254712345678", "712345678"]
    for t in tests:
        print(f"  {t} → {svc.format_phone(t)}")

    # Demo send
    result = svc.send_sms("+254712345678", "Hello from Smart Shamba!")
    print(f"\nSend result: {result}")

    print("\n✓ Africa's Talking service test completed!")

"""
Email Service for BloomWatch Kenya
Uses SendGrid for professional, beautiful email alerts
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# Try to import SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logging.warning("SendGrid not installed. Email service will use fallback mode.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    """
    Professional email service using SendGrid
    Sends beautiful, actionable emails to farmers
    """
    
    def __init__(self):
        """Initialize SendGrid client"""
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@bloomwatchkenya.com')
        self.from_name = os.getenv('SENDGRID_FROM_NAME', 'BloomWatch Kenya')
        
        if SENDGRID_AVAILABLE and self.api_key:
            try:
                self.client = SendGridAPIClient(self.api_key)
                logger.info("✓ SendGrid email service initialized successfully")
            except Exception as e:
                logger.warning(f"⚠ SendGrid initialization failed: {e}")
                self.client = None
        else:
            self.client = None
            if not SENDGRID_AVAILABLE:
                logger.warning("⚠ SendGrid module not installed. Install with: pip install sendgrid")
            else:
                logger.warning("⚠ SENDGRID_API_KEY not set. Running in demo mode.")
    
    def _create_welcome_email_html(self, farmer_data: Dict, bloom_data: Dict, language: str = 'en') -> str:
        """
        Create beautiful HTML email for welcome message
        """
        name = farmer_data.get('name', 'Farmer')
        county = farmer_data.get('county', 'Kenya')
        crops = farmer_data.get('crops', [])
        farm_size = farmer_data.get('farm_size', 0)
        
        # Bloom data
        ndvi_mean = bloom_data.get('ndvi_mean', 0.5)
        health_score = bloom_data.get('health_score', 50.0)
        bloom_risk = bloom_data.get('bloom_risk', 'Moderate')
        bloom_confidence = bloom_data.get('bloom_confidence', 0.5)
        
        # Risk color
        risk_colors = {'High': '#c62828', 'Moderate': '#f9a825', 'Low': '#2e7d32'}
        risk_color = risk_colors.get(bloom_risk, '#f9a825')
        
        # Crop list
        crop_list_html = ''.join([f'<li style="margin: 5px 0;">{crop.replace("_", " ").title()}</li>' for crop in crops[:5]])
        
        if language == 'sw':
            # Swahili version
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
                    <tr>
                        <td align="center">
                            <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                                
                                <!-- Header -->
                                <tr>
                                    <td style="background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%); padding: 40px 30px; text-align: center;">
                                        <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 700;">🌾 BloomWatch Kenya</h1>
                                        <p style="color: #e8f5e9; margin: 10px 0 0 0; font-size: 16px;">Teknolojia ya Satelaiti kwa Wakulima wa Kenya</p>
                                    </td>
                                </tr>
                                
                                <!-- Welcome Message -->
                                <tr>
                                    <td style="padding: 40px 30px;">
                                        <h2 style="color: #2e7d32; margin: 0 0 20px 0; font-size: 24px;">Karibu, {name}! 🎉</h2>
                                        <p style="color: #424242; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                            Hongera kwa kujiunga na BloomWatch Kenya, jukwaa la kisasa la kufuatilia afya ya mazao kwa kutumia data za satelaiti na akili bandia.
                                        </p>
                                        <p style="color: #424242; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            Tunatumia satelaiti za NASA, Sentinel-2, na teknolojia ya GPT-5 kukupatia taarifa sahihi na ushauri wa kilimo.
                                        </p>
                                        
                                        <!-- Farm Details Card -->
                                        <div style="background: #e8f5e9; border-left: 4px solid #2e7d32; padding: 20px; border-radius: 8px; margin: 0 0 30px 0;">
                                            <h3 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">📍 Maelezo ya Shamba Lako</h3>
                                            <table width="100%" cellpadding="5">
                                                <tr>
                                                    <td style="color: #616161; font-size: 14px;"><strong>Kaunti:</strong></td>
                                                    <td style="color: #424242; font-size: 14px;">{county}</td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #616161; font-size: 14px;"><strong>Ukubwa wa Shamba:</strong></td>
                                                    <td style="color: #424242; font-size: 14px;">{farm_size} Ekari</td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #616161; font-size: 14px; vertical-align: top;"><strong>Mazao:</strong></td>
                                                    <td style="color: #424242; font-size: 14px;">
                                                        <ul style="margin: 0; padding-left: 20px;">
                                                            {crop_list_html}
                                                        </ul>
                                                    </td>
                                                </tr>
                                            </table>
                                        </div>
                                        
                                        <!-- Current Bloom Status -->
                                        <div style="background: #f5f5f5; border-radius: 8px; padding: 25px; margin: 0 0 30px 0;">
                                            <h3 style="color: #2e7d32; margin: 0 0 20px 0; font-size: 18px;">🛰️ Hali ya Sasa ya Mazao</h3>
                                            
                                            <div style="margin: 0 0 15px 0;">
                                                <div style="color: #616161; font-size: 14px; margin-bottom: 5px;">Afya ya Mazao (Data za Satelaiti)</div>
                                                <div style="background: #e0e0e0; border-radius: 20px; height: 30px; position: relative; overflow: hidden;">
                                                    <div style="background: linear-gradient(90deg, #66bb6a 0%, #2e7d32 100%); height: 100%; width: {health_score}%; border-radius: 20px; display: flex; align-items: center; justify-content: center;">
                                                        <span style="color: #ffffff; font-weight: 700; font-size: 14px; z-index: 1;">{health_score:.0f}/100</span>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <div style="margin: 20px 0 0 0;">
                                                <table width="100%" cellpadding="10">
                                                    <tr>
                                                        <td style="background: #ffffff; border-radius: 8px; padding: 15px; width: 50%;">
                                                            <div style="color: #616161; font-size: 12px; margin-bottom: 5px;">Hatari ya Kuchanua</div>
                                                            <div style="color: {risk_color}; font-size: 20px; font-weight: 700;">{bloom_risk}</div>
                                                            <div style="color: #757575; font-size: 12px;">{bloom_confidence*100:.0f}% Uhakika</div>
                                                        </td>
                                                        <td style="width: 10px;"></td>
                                                        <td style="background: #ffffff; border-radius: 8px; padding: 15px; width: 50%;">
                                                            <div style="color: #616161; font-size: 12px; margin-bottom: 5px;">NDVI (Afya)</div>
                                                            <div style="color: #2e7d32; font-size: 20px; font-weight: 700;">{ndvi_mean:.2f}</div>
                                                            <div style="color: #757575; font-size: 12px;">Kati ya 0-1</div>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </div>
                                        </div>
                                        
                                        <!-- Call to Action -->
                                        <div style="text-align: center; margin: 30px 0 0 0;">
                                            <a href="http://localhost:8501" style="display: inline-block; background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%); color: #ffffff; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 12px rgba(46,125,50,0.3);">
                                                🚀 Fungua Dashboard Yako
                                            </a>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- Features Section -->
                                <tr>
                                    <td style="background: #f9fbe7; padding: 30px;">
                                        <h3 style="color: #2e7d32; margin: 0 0 20px 0; font-size: 18px; text-align: center;">Nini Unaweza Kufanya 🌟</h3>
                                        <table width="100%" cellpadding="10">
                                            <tr>
                                                <td width="33%" style="text-align: center;">
                                                    <div style="font-size: 36px; margin-bottom: 10px;">🛰️</div>
                                                    <div style="color: #424242; font-size: 14px; font-weight: 600;">Data za Satelaiti</div>
                                                    <div style="color: #757575; font-size: 12px;">Fuatilia mazao kila siku</div>
                                                </td>
                                                <td width="33%" style="text-align: center;">
                                                    <div style="font-size: 36px; margin-bottom: 10px;">🤖</div>
                                                    <div style="color: #424242; font-size: 14px; font-weight: 600;">Flora AI</div>
                                                    <div style="color: #757575; font-size: 12px;">Uliza maswali yoyote</div>
                                                </td>
                                                <td width="33%" style="text-align: center;">
                                                    <div style="font-size: 36px; margin-bottom: 10px;">📱</div>
                                                    <div style="color: #424242; font-size: 14px; font-weight: 600;">Arifa za SMS</div>
                                                    <div style="color: #757575; font-size: 12px;">Taarifa za haraka</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Footer -->
                                <tr>
                                    <td style="background: #2e7d32; padding: 30px; text-align: center;">
                                        <p style="color: #e8f5e9; margin: 0 0 10px 0; font-size: 14px;">
                                            Ungana na maelfu ya wakulima wanaotumia teknolojia ya kisasa kupandisha mavuno.
                                        </p>
                                        <p style="color: #a5d6a7; margin: 0; font-size: 12px;">
                                            © 2025 BloomWatch Kenya | Imetumia NASA, Sentinel-2, na OpenAI GPT-5
                                        </p>
                                        <p style="color: #a5d6a7; margin: 10px 0 0 0; font-size: 12px;">
                                            Maswali? Wasiliana nasi: support@bloomwatchkenya.com
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
        else:
            # English version
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
                    <tr>
                        <td align="center">
                            <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                                
                                <!-- Header -->
                                <tr>
                                    <td style="background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%); padding: 40px 30px; text-align: center;">
                                        <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 700;">🌾 BloomWatch Kenya</h1>
                                        <p style="color: #e8f5e9; margin: 10px 0 0 0; font-size: 16px;">Satellite Intelligence for Kenyan Farmers</p>
                                    </td>
                                </tr>
                                
                                <!-- Welcome Message -->
                                <tr>
                                    <td style="padding: 40px 30px;">
                                        <h2 style="color: #2e7d32; margin: 0 0 20px 0; font-size: 24px;">Welcome, {name}! 🎉</h2>
                                        <p style="color: #424242; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                            Congratulations on joining BloomWatch Kenya, the cutting-edge platform that uses satellite data and artificial intelligence to monitor crop health.
                                        </p>
                                        <p style="color: #424242; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            We use NASA satellites, Sentinel-2, and GPT-5 technology to provide you with accurate insights and agricultural advice.
                                        </p>
                                        
                                        <!-- Farm Details Card -->
                                        <div style="background: #e8f5e9; border-left: 4px solid #2e7d32; padding: 20px; border-radius: 8px; margin: 0 0 30px 0;">
                                            <h3 style="color: #2e7d32; margin: 0 0 15px 0; font-size: 18px;">📍 Your Farm Details</h3>
                                            <table width="100%" cellpadding="5">
                                                <tr>
                                                    <td style="color: #616161; font-size: 14px;"><strong>County:</strong></td>
                                                    <td style="color: #424242; font-size: 14px;">{county}</td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #616161; font-size: 14px;"><strong>Farm Size:</strong></td>
                                                    <td style="color: #424242; font-size: 14px;">{farm_size} Acres</td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #616161; font-size: 14px; vertical-align: top;"><strong>Crops:</strong></td>
                                                    <td style="color: #424242; font-size: 14px;">
                                                        <ul style="margin: 0; padding-left: 20px;">
                                                            {crop_list_html}
                                                        </ul>
                                                    </td>
                                                </tr>
                                            </table>
                                        </div>
                                        
                                        <!-- Current Bloom Status -->
                                        <div style="background: #f5f5f5; border-radius: 8px; padding: 25px; margin: 0 0 30px 0;">
                                            <h3 style="color: #2e7d32; margin: 0 0 20px 0; font-size: 18px;">🛰️ Current Crop Status</h3>
                                            
                                            <div style="margin: 0 0 15px 0;">
                                                <div style="color: #616161; font-size: 14px; margin-bottom: 5px;">Crop Health (Satellite Data)</div>
                                                <div style="background: #e0e0e0; border-radius: 20px; height: 30px; position: relative; overflow: hidden;">
                                                    <div style="background: linear-gradient(90deg, #66bb6a 0%, #2e7d32 100%); height: 100%; width: {health_score}%; border-radius: 20px; display: flex; align-items: center; justify-content: center;">
                                                        <span style="color: #ffffff; font-weight: 700; font-size: 14px; z-index: 1;">{health_score:.0f}/100</span>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <div style="margin: 20px 0 0 0;">
                                                <table width="100%" cellpadding="10">
                                                    <tr>
                                                        <td style="background: #ffffff; border-radius: 8px; padding: 15px; width: 50%;">
                                                            <div style="color: #616161; font-size: 12px; margin-bottom: 5px;">Bloom Risk</div>
                                                            <div style="color: {risk_color}; font-size: 20px; font-weight: 700;">{bloom_risk}</div>
                                                            <div style="color: #757575; font-size: 12px;">{bloom_confidence*100:.0f}% Confidence</div>
                                                        </td>
                                                        <td style="width: 10px;"></td>
                                                        <td style="background: #ffffff; border-radius: 8px; padding: 15px; width: 50%;">
                                                            <div style="color: #616161; font-size: 12px; margin-bottom: 5px;">NDVI (Health)</div>
                                                            <div style="color: #2e7d32; font-size: 20px; font-weight: 700;">{ndvi_mean:.2f}</div>
                                                            <div style="color: #757575; font-size: 12px;">Range: 0-1</div>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </div>
                                        </div>
                                        
                                        <!-- Call to Action -->
                                        <div style="text-align: center; margin: 30px 0 0 0;">
                                            <a href="http://localhost:8501" style="display: inline-block; background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%); color: #ffffff; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 12px rgba(46,125,50,0.3);">
                                                🚀 Open Your Dashboard
                                            </a>
                                        </div>
                                    </td>
                                </tr>
                                
                                <!-- Features Section -->
                                <tr>
                                    <td style="background: #f9fbe7; padding: 30px;">
                                        <h3 style="color: #2e7d32; margin: 0 0 20px 0; font-size: 18px; text-align: center;">What You Can Do 🌟</h3>
                                        <table width="100%" cellpadding="10">
                                            <tr>
                                                <td width="33%" style="text-align: center;">
                                                    <div style="font-size: 36px; margin-bottom: 10px;">🛰️</div>
                                                    <div style="color: #424242; font-size: 14px; font-weight: 600;">Satellite Data</div>
                                                    <div style="color: #757575; font-size: 12px;">Track crops daily</div>
                                                </td>
                                                <td width="33%" style="text-align: center;">
                                                    <div style="font-size: 36px; margin-bottom: 10px;">🤖</div>
                                                    <div style="color: #424242; font-size: 14px; font-weight: 600;">Flora AI</div>
                                                    <div style="color: #757575; font-size: 12px;">Ask any question</div>
                                                </td>
                                                <td width="33%" style="text-align: center;">
                                                    <div style="font-size: 36px; margin-bottom: 10px;">📱</div>
                                                    <div style="color: #424242; font-size: 14px; font-weight: 600;">SMS Alerts</div>
                                                    <div style="color: #757575; font-size: 12px;">Instant updates</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Footer -->
                                <tr>
                                    <td style="background: #2e7d32; padding: 30px; text-align: center;">
                                        <p style="color: #e8f5e9; margin: 0 0 10px 0; font-size: 14px;">
                                            Join thousands of farmers using modern technology to increase their yields.
                                        </p>
                                        <p style="color: #a5d6a7; margin: 0; font-size: 12px;">
                                            © 2025 BloomWatch Kenya | Powered by NASA, Sentinel-2, and OpenAI GPT-5
                                        </p>
                                        <p style="color: #a5d6a7; margin: 10px 0 0 0; font-size: 12px;">
                                            Questions? Contact us: support@bloomwatchkenya.com
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
        
        return html
    
    def _create_alert_email_html(self, farmer_data: Dict, alert_data: Dict, language: str = 'en') -> str:
        """
        Create beautiful HTML email for bloom/climate alerts
        """
        name = farmer_data.get('name', 'Farmer')
        county = farmer_data.get('county', 'Kenya')
        crop = alert_data.get('crop', 'crops')
        
        # Alert data
        health_score = alert_data.get('health_score', 50.0)
        bloom_risk = alert_data.get('bloom_risk', 'Moderate')
        advice = alert_data.get('advice', 'Monitor your crops carefully.')
        data_source = alert_data.get('data_source', 'Satellite')
        ndvi = alert_data.get('ndvi', 0.5)
        
        # Risk color
        risk_colors = {'High': '#c62828', 'Moderate': '#f9a825', 'Low': '#2e7d32'}
        risk_color = risk_colors.get(bloom_risk, '#f9a825')
        risk_emoji = {'High': '🔴', 'Moderate': '🟡', 'Low': '🟢'}.get(bloom_risk, '🟡')
        
        if language == 'sw':
            subject = f"🌾 Arifa: Hali ya Mazao katika {county}"
            title = "Arifa ya Hali ya Mazao"
            greeting = f"Habari {name},"
            health_label = "Afya ya Mazao"
            risk_label = "Hatari ya Kuchanua"
            advice_label = "Ushauri wa Flora AI"
            cta_text = "Angalia Dashboard"
        else:
            subject = f"🌾 Alert: Crop Status in {county}"
            title = "Crop Status Alert"
            greeting = f"Hello {name},"
            health_label = "Crop Health"
            risk_label = "Bloom Risk"
            advice_label = "Flora AI Advice"
            cta_text = "View Dashboard"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%); padding: 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">🌾 BloomWatch Kenya</h1>
                                    <p style="color: #e8f5e9; margin: 10px 0 0 0; font-size: 14px;">{title}</p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 30px;">
                                    <p style="color: #424242; font-size: 16px; margin: 0 0 20px 0;">{greeting}</p>
                                    
                                    <!-- Alert Card -->
                                    <div style="background: #f5f5f5; border-radius: 8px; padding: 20px; margin: 0 0 20px 0;">
                                        <div style="color: #616161; font-size: 14px; margin-bottom: 5px;">{health_label} - {crop.title()}</div>
                                        <div style="background: #e0e0e0; border-radius: 20px; height: 25px; margin: 0 0 15px 0;">
                                            <div style="background: linear-gradient(90deg, #66bb6a 0%, #2e7d32 100%); height: 100%; width: {health_score}%; border-radius: 20px; display: flex; align-items: center; justify-content: center;">
                                                <span style="color: #ffffff; font-weight: 700; font-size: 12px;">{health_score:.0f}/100</span>
                                            </div>
                                        </div>
                                        
                                        <table width="100%" cellpadding="10">
                                            <tr>
                                                <td style="background: #ffffff; border-radius: 8px; padding: 15px;">
                                                    <div style="color: #616161; font-size: 12px;">{risk_label}</div>
                                                    <div style="color: {risk_color}; font-size: 18px; font-weight: 700; margin-top: 5px;">{risk_emoji} {bloom_risk}</div>
                                                </td>
                                                <td style="width: 10px;"></td>
                                                <td style="background: #ffffff; border-radius: 8px; padding: 15px;">
                                                    <div style="color: #616161; font-size: 12px;">NDVI</div>
                                                    <div style="color: #2e7d32; font-size: 18px; font-weight: 700; margin-top: 5px;">{ndvi:.2f}</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <!-- Advice Section -->
                                    <div style="background: #e3f2fd; border-left: 4px solid #1976d2; padding: 20px; border-radius: 8px; margin: 0 0 20px 0;">
                                        <h3 style="color: #1976d2; margin: 0 0 10px 0; font-size: 16px;">💡 {advice_label}</h3>
                                        <p style="color: #424242; font-size: 14px; line-height: 1.5; margin: 0;">{advice}</p>
                                    </div>
                                    
                                    <!-- CTA -->
                                    <div style="text-align: center;">
                                        <a href="http://localhost:8501" style="display: inline-block; background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%); color: #ffffff; text-decoration: none; padding: 12px 30px; border-radius: 8px; font-size: 14px; font-weight: 600;">
                                            {cta_text} →
                                        </a>
                                    </div>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background: #f5f5f5; padding: 20px; text-align: center;">
                                    <p style="color: #757575; margin: 0; font-size: 12px;">
                                        © 2025 BloomWatch Kenya | Data: {data_source}
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        return html
    
    def send_welcome_email(self, farmer_data: Dict, bloom_data: Dict) -> Dict:
        """
        Send welcome email to newly registered farmer
        """
        if not self.client:
            logger.warning("SendGrid client not available. Email not sent.")
            return {'success': False, 'error': 'SendGrid not configured'}
        
        email = farmer_data.get('email')
        if not email:
            logger.warning("No email address provided")
            return {'success': False, 'error': 'No email address'}
        
        language = farmer_data.get('language', 'en')
        name = farmer_data.get('name', 'Farmer')
        
        # Subject
        if language == 'sw':
            subject = f"🌾 Karibu BloomWatch Kenya, {name}!"
        else:
            subject = f"🌾 Welcome to BloomWatch Kenya, {name}!"
        
        # Generate HTML
        html_content = self._create_welcome_email_html(farmer_data, bloom_data, language)
        
        # Create message
        message = Mail(
            from_email=Email(self.from_email, self.from_name),
            to_emails=To(email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        try:
            response = self.client.send(message)
            logger.info(f"✓ Welcome email sent to {email} (Status: {response.status_code})")
            return {
                'success': True,
                'email': email,
                'status_code': response.status_code
            }
        except Exception as e:
            logger.error(f"✗ Failed to send welcome email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_alert_email(self, farmer_data: Dict, alert_data: Dict) -> Dict:
        """
        Send crop alert email to farmer
        """
        if not self.client:
            logger.warning("SendGrid client not available. Email not sent.")
            return {'success': False, 'error': 'SendGrid not configured'}
        
        email = farmer_data.get('email')
        if not email:
            logger.warning("No email address provided")
            return {'success': False, 'error': 'No email address'}
        
        language = farmer_data.get('language', 'en')
        county = farmer_data.get('county', 'Kenya')
        
        # Subject
        if language == 'sw':
            subject = f"🌾 Arifa: Hali ya Mazao katika {county}"
        else:
            subject = f"🌾 Alert: Crop Status in {county}"
        
        # Generate HTML
        html_content = self._create_alert_email_html(farmer_data, alert_data, language)
        
        # Create message
        message = Mail(
            from_email=Email(self.from_email, self.from_name),
            to_emails=To(email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        try:
            response = self.client.send(message)
            logger.info(f"✓ Alert email sent to {email} (Status: {response.status_code})")
            return {
                'success': True,
                'email': email,
                'status_code': response.status_code
            }
        except Exception as e:
            logger.error(f"✗ Failed to send alert email: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Testing
if __name__ == "__main__":
    print("📧 Email Service Test")
    print("=" * 70)
    
    service = EmailService()
    
    # Test farmer data
    farmer_data = {
        'name': 'John Kamau',
        'email': 'test@example.com',
        'county': 'Kiambu',
        'crops': ['maize', 'beans', 'coffee'],
        'farm_size': 5.5,
        'language': 'en'
    }
    
    # Test bloom data
    bloom_data = {
        'ndvi_mean': 0.72,
        'health_score': 85.0,
        'bloom_risk': 'High',
        'bloom_confidence': 0.78
    }
    
    # Generate HTML preview
    print("\n📧 Generating Welcome Email HTML...")
    html = service._create_welcome_email_html(farmer_data, bloom_data, 'en')
    print(f"✓ HTML generated ({len(html)} characters)")
    
    print("\n📧 Generating Alert Email HTML...")
    alert_data = {
        'crop': 'maize',
        'health_score': 85.0,
        'bloom_risk': 'High',
        'ndvi': 0.72,
        'advice': 'Your maize shows excellent health! Maintain current irrigation. Watch for tasseling stage.',
        'data_source': 'Sentinel-2'
    }
    html_alert = service._create_alert_email_html(farmer_data, alert_data, 'en')
    print(f"✓ Alert HTML generated ({len(html_alert)} characters)")
    
    print("\n" + "=" * 70)
    print("✅ Email Service test complete!")
    print("\nTo actually send emails:")
    print("1. Install SendGrid: pip install sendgrid")
    print("2. Set SENDGRID_API_KEY in .env")
    print("3. Set SENDGRID_FROM_EMAIL in .env")



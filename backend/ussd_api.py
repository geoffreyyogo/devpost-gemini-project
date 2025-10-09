"""
Flask API server for Africa's Talking USSD callbacks
"""

from flask import Flask, request, Response
from africastalking_service import AfricasTalkingService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
at_service = AfricasTalkingService()

@app.route('/ussd', methods=['POST','GET'])
def ussd_callback():
    """
    USSD callback endpoint for Africa's Talking
    This endpoint receives USSD requests and returns appropriate responses
    """
    try:
        # Get USSD parameters from Africa's Talking
        session_id = request.values.get('sessionId', None)
        service_code = request.values.get('serviceCode', None)
        phone_number = request.values.get('phoneNumber', None)
        text = request.values.get('text', '')
        
        logger.info(f"USSD Request - Phone: {phone_number}, Text: {text}")
        
        # Handle USSD request
        response_text = at_service.handle_ussd_request(
            session_id, 
            service_code, 
            phone_number, 
            text
        )
        
        # Return response to Africa's Talking
        return Response(response_text, mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"Error handling USSD request: {e}")
        return Response("END An error occurred. Please try again later.", mimetype='text/plain')

@app.route('/delivery-reports', methods=['POST'])
def sms_delivery_report():
    """
    SMS delivery report callback from Africa's Talking
    This endpoint receives SMS delivery status updates
    """
    try:
        # Get delivery report parameters
        phone_number = request.values.get('phoneNumber', None)
        status = request.values.get('status', None)
        network_code = request.values.get('networkCode', None)
        
        logger.info(f"SMS Delivery Report - Phone: {phone_number}, Status: {status}, Network: {network_code}")
        
        # You can store this in MongoDB or use for analytics
        # For now, just log it
        
        return Response('Received', mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"Error handling delivery report: {e}")
        return Response('Error', mimetype='text/plain')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'BloomWatch Kenya USSD API'}

@app.route('/test-ussd', methods=['GET'])
def test_ussd():
    """Test USSD flow (for development)"""
    return '''
    <html>
    <head><title>BloomWatch Kenya - USSD Test</title></head>
    <body style="font-family: Arial; max-width: 600px; margin: 50px auto;">
        <h1>🌾 BloomWatch Kenya - USSD Test</h1>
        <p>Use this form to simulate USSD requests for testing.</p>
        
        <form action="/ussd" method="POST">
            <label>Session ID:</label><br>
            <input type="text" name="sessionId" value="test_session" style="width: 100%; padding: 8px; margin: 8px 0;"><br>
            
            <label>Service Code:</label><br>
            <input type="text" name="serviceCode" value="*384*1234#" style="width: 100%; padding: 8px; margin: 8px 0;"><br>
            
            <label>Phone Number:</label><br>
            <input type="text" name="phoneNumber" value="+254712345678" style="width: 100%; padding: 8px; margin: 8px 0;"><br>
            
            <label>Text (USSD input):</label><br>
            <input type="text" name="text" value="" placeholder="e.g., 1*John Kamau*1*1,2*1" style="width: 100%; padding: 8px; margin: 8px 0;"><br>
            
            <button type="submit" style="padding: 10px 20px; margin-top: 10px; background: #28a745; color: white; border: none; cursor: pointer;">
                Submit USSD Request
            </button>
        </form>
        
        <hr style="margin: 30px 0;">
        
        <h3>USSD Flow Example:</h3>
        <ol>
            <li>Initial: <code>text=""</code> → Shows language menu</li>
            <li>Select English: <code>text="1"</code> → Asks for name</li>
            <li>Enter name: <code>text="1*John Kamau"</code> → Asks for region</li>
            <li>Select Central: <code>text="1*John Kamau*1"</code> → Asks for crops</li>
            <li>Select Maize, Beans: <code>text="1*John Kamau*1*1,2"</code> → Shows confirmation</li>
            <li>Confirm: <code>text="1*John Kamau*1*1,2*1"</code> → Completes registration</li>
        </ol>
        
        <h3>📊 Quick Stats:</h3>
        <p><a href="/stats" target="_blank">View Farmer Statistics</a></p>
    </body>
    </html>
    '''

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get farmer statistics"""
    stats = at_service.mongo.get_farmer_statistics()
    
    html = f'''
    <html>
    <head><title>BloomWatch Kenya - Statistics</title></head>
    <body style="font-family: Arial; max-width: 800px; margin: 50px auto;">
        <h1>🌾 BloomWatch Kenya - Statistics</h1>
        
        <div style="background: #f0f0f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h2>👨‍🌾 Farmer Statistics</h2>
            <p><strong>Total Farmers:</strong> {stats.get('total_farmers', 0)}</p>
            <p><strong>Active Farmers:</strong> {stats.get('active_farmers', 0)}</p>
            <p><strong>Total Alerts Sent:</strong> {stats.get('total_alerts_sent', 0)}</p>
        </div>
        
        <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>📍 Farmers by Region</h3>
            <ul>
                {''.join(f"<li><strong>{region.replace('_', ' ').title()}:</strong> {count}</li>" 
                         for region, count in stats.get('farmers_by_region', {}).items())}
            </ul>
        </div>
        
        <div style="background: #fff3e0; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🌾 Farmers by Crop</h3>
            <ul>
                {''.join(f"<li><strong>{crop.title()}:</strong> {count}</li>" 
                         for crop, count in stats.get('farmers_by_crop', {}).items())}
            </ul>
        </div>
        
        <p><a href="/test-ussd">← Back to USSD Test</a></p>
    </body>
    </html>
    '''
    
    return html

if __name__ == '__main__':
    print("🌾 BloomWatch Kenya - USSD API Server")
    print("=" * 60)
    print("Starting Flask server...")
    print("USSD Endpoint: http://localhost:5000/ussd")
    print("Test Interface: http://localhost:5000/test-ussd")
    print("Statistics: http://localhost:5000/stats")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)


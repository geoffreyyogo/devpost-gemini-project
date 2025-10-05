# Procfile for alternative deployments (Heroku, etc.)
# Render uses render.yaml instead, but this is useful for other platforms

# Main web app
web: streamlit run app/streamlit_app_enhanced.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true

# Admin dashboard (if deploying as single app)
# admin: streamlit run app/admin_dashboard.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true

# USSD API
ussd: cd backend && gunicorn ussd_api:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120


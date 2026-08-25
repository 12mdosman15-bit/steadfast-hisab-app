# Steadfast Business হিসাব — Ready Railway build

Files: app.py, geo_data.py, index.html, requirements.txt, Procfile, runtime.txt.

Important Railway variables:
- APP_SECRET = a long random secret
- DATABASE_URL = Railway PostgreSQL connection string (recommended)
- Optional STEADFAST_BASE_URL = https://portal.packzy.com/api/v1

Each user registers/logs in and saves their own Steadfast API Key + Secret Key. Orders, expenses and supplier payments are scoped to the logged-in user.

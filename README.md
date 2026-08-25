# 📊 অর্ডার হিসাব — Steadfast Business Manager

A mobile-first multi-user Steadfast parcel/business manager.

## Included
- Beautiful blue mobile dashboard inspired by the previous app layout
- Separate login/account and user-isolated data
- Per-user Steadfast API Key + Secret Key
- Steadfast parcel create + status refresh
- CN# / Consignment ID + Tracking ID display
- English District + Thana / Upazila dropdowns
- Orders, Expenses, Suppliers and Profit dashboard
- Railway-ready Flask app

## Railway
1. Upload this folder to GitHub.
2. Deploy the repository on Railway.
3. Set `APP_SECRET` to a long random value.
4. Start command is already defined by `Procfile`.
5. Open the app, create an account, then go to Settings and add that user's Steadfast API credentials.

Do not open `templates/index.html` directly from the phone. The app must run through Flask/Railway so `/static/*`, `/api/*` and the database work.

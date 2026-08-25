Steadfast Business - Backup & Restore

1. Deploy the files normally on Railway.
2. Open the app and use Backup & Restore.
3. Download Backup creates steadfast_business_backup.json.
4. Keep this file somewhere safe.
5. Restore Backup uploads that JSON and restores orders, expenses and supplier payments.
6. Existing orders with the same invoice are updated instead of duplicated.

Important: if you later add strict multi-user authentication, scope /api/backup and /api/restore to the logged-in user's user_id before production use.

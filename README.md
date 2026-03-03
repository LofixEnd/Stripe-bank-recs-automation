# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python app.py

# 3. Open in browser
# Navigate to: http://localhost:5000# Stripe Reconciliation Accelerator - README

## Overview

The **Stripe Reconciliation Accelerator** is a web-based application designed for eCommerce bookkeeping firms to automate the tedious process of matching Stripe settlements to bank deposits. This tool reduces manual reconciliation time by 50-70% through intelligent matching algorithms and exception detection.

## Features

### 🎯 Core Functionality
- **Automated Matching**: Match Stripe payouts to bank deposits using a configurable tolerance, date proximity (±3 days) and description filtering. Supports exact, probable, combined and split matches.
- **Exception Detection**: Identify mismatches, missing or excess deposits, duplicate payouts, timing differences, and amount variances beyond tolerance
- **Multi-Client Support**: Slug-based access system for client isolation
- **Secure Processing**: In-memory file handling with no persistent data storage
- **Professional Reports**: Multi-sheet Excel reports with executive summaries

### 🔒 Security & Privacy
- Client isolation via unique URL slugs (e.g., `/portal/client_a`)
- Files processed in-memory and deleted immediately after report generation
- No client data persists on the server
- CSRF protection and security headers

### 📊 Report Outputs
The tool generates a comprehensive Excel file (`reconciliation_report.xlsx`) with four tabs:

1. **Executive Summary**: High-level totals
   - Total Charges, Refunds, Fees, Disputes
   - Net Activity calculation
   - Exception count summary

2. **Payout Matching**: Detailed payout analysis
   - Stripe Amount vs Bank Amount
   - Match Status (Matched/Mismatch)
   - All payout transactions listed

3. **Exceptions**: Critical discrepancies
   - Payout amount mismatches
   - Missing payouts in bank statement
   - Negative balances and orphaned transactions

4. **Audit Log**: Transaction-level details
   - All matching operations
   - Flagged issues and warnings
   - Timestamp and event tracking

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Local Setup

1. **Clone/Download** the application:
   ```bash
   cd stripe-reconciliation-accelerator
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Access the application**:
   Open your browser and navigate to: `http://localhost:5000`

## Authentication & User Management

The portal now requires users to log in.  Each account is tied to a
single `client_slug` and users cannot view or upload data for any other
client.  Passwords are hashed with Werkzeug and sessions are protected
with Flask-Login and CSRF tokens from Flask-WTF.

To create the first (administrative) user run the helper script:

```bash
python create_user.py
```

Subsequent accounts can either be created via the `/register` route by an
admin user or by re‑running the script.  When migrating from the previous
slug‑only system you should:

1. List all slugs you have been using (see `VALID_CLIENTS` in `app.py`).
2. Create a user for each slug using the script or the dashboard.
   Example:
   ```bash
   python create_user.py  # enter "client_a" when prompted for slug
   ```
3. Update clients in the database as needed; the `VALID_CLIENTS` dict is
   still used for display names but can eventually be replaced with a
   database table.

Once users exist, access to `/portal/<slug>` will redirect to the login
page for unauthenticated visitors and return **403 Forbidden** if the
logged–in account does not own that slug.

## Usage

### Uploading Files

The application requires three CSV files:

#### 1. Stripe Balance CSV
Contains your current account balance breakdown.

**Required Columns**:
- `Payout ID` - Unique identifier for each payout
- `Charge Amount` - Total charges
- `Refund Amount` - Total refunds
- `Fee Amount` - Stripe fees
- `Dispute Amount` - Chargeback disputes
- `Date` - Transaction date

**Sample Format**:
```
Date,Payout ID,Charge Amount,Refund Amount,Fee Amount,Dispute Amount,Balance
2024-02-28,payout_001,5000.00,-200.00,-120.50,0.00,4679.50
```

#### 2. Stripe Payouts CSV
Lists all payout transactions from Stripe.

**Required Columns**:
- `Payout ID` - Unique payout identifier
- `Payout Date` - Date the payout was initiated
- `Payout Amount` - Amount paid out
- `Currency` - USD, EUR, etc.
- `Status` - paid, pending, etc.
- `Destination` - Bank account details

**Sample Format**:
```
Payout ID,Payout Date,Payout Amount,Currency,Status,Destination,Arrival Date
payout_001,2024-02-27,4679.50,USD,paid,Bank Account ****3210,2024-02-28
```

#### 3. Bank Statement CSV
Your bank account transactions filtered for Stripe deposits.

**Required Columns**:
- `Date` - Transaction date
- `Description` - Transaction description (must include "Stripe")
- `Credit/Deposit Amount` - Amount received
- `Balance` - Running account balance
- `Reference` - Transaction reference number

**Sample Format**:
```
Date,Description,Debit,Credit,Balance,Reference
2024-02-28,STRIPE TRANSFER 12345,0.00,4679.50,125678.50,REF001
```

### Processing Reconciliation

1. **Select your client portal** from the home page
2. **Drag and drop** (or click to browse) your three CSV files
3. **Review the preview** of loaded data
4. **Click "Process & Download Report"** to generate the Excel file
5. **Download automatically** starts when ready

### Interpreting Results

#### Status Indicators
- ✓ **Matched**: Payout found in bank statement with matching amount
- ⚠️ **Mismatch**: Payout found but amount differs from bank record
- ❌ **Missing**: Payout in Stripe but not in bank statement

#### Exception Types
- **Amount Mismatch**: Stripe amount ≠ Bank amount
- **Negative Balance**: Account balance below zero
- **Orphaned Transaction**: Bank deposit with no matching payout
- **Missing Payout**: Payout ID in balance but not in payouts file

## Deployment

### Deploying to Render.com

1. **Create Render account** at https://render.com

2. **Connect your repository** (GitHub/GitLab)

3. **Create new Web Service**:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
   - Environment: Select Python 3.x runtime

4. **Set Environment Variables**:
   - `FLASK_ENV=production`
   - `SECRET_KEY=your-secret-key-here`

5. **Deploy**: Render automatically deploys on code changes

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

Build and run:
```bash
docker build -t stripe-recon .
docker run -p 5000:5000 stripe-recon
```

## Project Structure

```
stripe-reconciliation-accelerator/
├── app.py                 # Flask application and routes
├── logic.py              # Core reconciliation engine
├── requirements.txt      # Python dependencies
├── Procfile             # Render deployment configuration
├── .env.example         # Environment variables template
├── templates/           # HTML templates
│   ├── base.html       # Base template with styling
│   ├── index.html      # Client selection page
│   └── portal.html     # Main reconciliation interface
├── static/             # Static assets (CSS, JS)
├── uploads/            # Temporary file storage (auto-cleaned)
└── sample_data/        # Example CSV files for testing
    ├── stripe_balance.csv
    ├── stripe_payouts.csv
    └── bank_statement.csv
```

## API Reference

### Endpoints

#### GET `/`
Home page with client selection.

#### GET `/portal/<client_slug>`
Main client portal.
- `client_slug`: Unique identifier for client (e.g., `client_a`)

#### POST `/api/portal/<client_slug>/upload`
Upload a CSV file.
- **Form Data**:
  - `file`: CSV file
  - `file_type`: 'balance', 'payout', or 'bank'

#### GET `/api/portal/<client_slug>/status`
Get reconciliation status.
- **Response**: Upload status for each file type

#### POST `/api/portal/<client_slug>/process`
Process reconciliation and download report.
- **Response**: Excel file download

#### POST `/api/portal/<client_slug>/reset`
Clear session and uploaded files.

#### GET `/api/portal/<client_slug>/preview`
Get preview of loaded data.

## Troubleshooting

### Issue: "Invalid client" error
**Solution**: Client slug must be valid. Check `VALID_CLIENTS` dictionary in `app.py`.

### Issue: "File format error"
**Solution**: Ensure CSV files use proper encoding (UTF-8) and contain required columns.

### Issue: "Empty dataset"
**Solution**: Files may not contain "Stripe" in bank statement descriptions. Add "Stripe" to description field.

### Issue: Large files timing out
**Solution**: Increase Flask timeout or process smaller date ranges. Max file size is 50MB.

## Future Enhancements

### Planned Features (TODO)
- ✅ Multi-currency support conversion (`convert_to_base_currency()`)
- ✅ Shopify revenue comparison (`compare_with_shopify_sales()`)
- ✅ Opening balance adjustments (`adjust_for_opening_balance()`)
- 🔄 Database integration for historical reports
- 🔄 Automated email delivery of reports
- 🔄 Multi-user roles and permissions
- 🔄 API for third-party integrations
- 🔄 Scheduled reconciliation automation
- 🔄 Advanced analytics dashboard

## License

This project is built for eCommerce bookkeeping firms. Contact for licensing details.

## Support

For issues, feature requests, or questions:
- Email: support@striperecon.com
- Documentation: https://docs.striperecon.com

## Changelog

### Version 1.0 (February 2026)
- Initial release
- Core reconciliation matching
- Exception detection
- Multi-client support
- Excel report generation

---

**Built with ❤️ for bookkeeping professionals**

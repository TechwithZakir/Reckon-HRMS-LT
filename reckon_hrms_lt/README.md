# Reckon HRMS (simple_hrms)

A simple, user-friendly HRMS application for Frappe/ERPNext v16.

## Philosophy

> **Simple HR experience + Frappe HR attendance + optional biometric integration + native ERPNext Accounting**

This app is intended for **average HR/admin users** who need a straightforward salary workflow without understanding Salary Structures, Salary Components, Payroll Entries, or GL Entries.

## Architecture

```
Frappe HR
  ├── Employee (standard, adds gross_salary custom field)
  ├── Employee Checkin (standard)
  └── Attendance (standard)

Reckon HRMS
  ├── Reckon HRMS Settings
  ├── Biometric Device + Biometric Sync Log
  ├── Salary Payment (single) + Bulk Salary Payment
  ├── Biometric Adapter Framework (ZKTeco placeholder)
  ├── Automated Attendance Processing
  └── Payslip Print Format
         ↓
  ERPNext Accounting (Journal Entry + Payment Entry)
```

### Why Journal Entry + Payment Entry instead of Payroll Entry?

The core spec requires users to never need to understand:
- Salary Structure
- Salary Component
- Payroll Entry
- GL Entry

ERPNext's Payroll Entry mandates a Salary Structure Assignment for every employee, plus at least one Salary Structure with configured components. This adds significant complexity that contradicts the "simple" philosophy.

This app uses **native ERPNext accounting directly**:
1. **Accrual**: Journal Entry (Salary Expense Dr / Salary Payable Cr)
2. **Payment**: Journal Entry (Salary Payable Dr / Bank or Cash Cr)

This approach:
- Uses standard ERPNext DocTypes
- Follows Expense → Payable → Bank/Cash conceptually
- Requires zero payroll configuration from the HR user
- Is fully cancellable with audit trail via ERPNext's standard cancellation

## Features

- **Employee**: Uses standard Frappe HR Employee (with `gross_salary` custom field added)
- **Attendance**: Reads from standard Frappe HR Attendance + Employee Checkin
- **Biometric Integration**: Adapter-based framework (ZKTeco placeholder, extensible for more vendors)
- **Salary Payment**: Simple per-employee salary processing with editable gross, allowances, bonuses, deductions
- **Bulk Salary**: Process all employees at once with editable columns
- **Accounting**: Native ERPNext Journal Entry + Payment Entry posted automatically on "Pay"
- **Payslip**: Professional printable/printable PDF payslip via Jinja print format
- **Reports**: Attendance Report, Salary Report, Biometric Sync Report
- **Dashboard**: Number cards on the Reckon HRMS workspace
- **Permissions**: System Manager (full), HR Manager (full), HR User (no settings)

## Workflow

```
Employee → Attendance / Biometric → Salary → Enter Gross → Add Allowance/Bonus → Calculate → Pay → Auto Accounting → Print Payslip
```

## Installation

### Prerequisites
- Frappe Framework v16
- ERPNext v16
- Frappe HR v16 (hrms)
- Bench CLI installed and running on your VPS/server

### Install the app

```bash

# Navigate to your bench directory

# Get the app (replace with actual repo URL)
bench get-app reckon_hrms_lt <repo-url>

# Install into your site
bench --site <site-name> install-app reckon_hrms_lt

# Migrate
bench --site <site-name> migrate

# Clear cache
bench clear-cache

# Restart
bench restart
```

### Post-installation Setup

1. Go to **Reckon HRMS Settings**
2. Configure:
   - Working Days (default 30)
   - Late Threshold Minutes (default 15)
   - Late Count for Deduction (e.g. 3 Late = 1 Day)
   - Absent / Half Day deduction multipliers
3. Under **Accounting Settings**:
   - Company
   - Salary Expense Account
   - Salary Payable Account
   - Default Bank Account
   - Default Cash Account
   - Cost Center

## Background Jobs

| Schedule | Job | Purpose |
|----------|-----|---------|
| Hourly | `sync_biometric_devices` | Sync all enabled biometric devices |
| Daily | `process_auto_attendance` | Create Attendance records from yesterday's checkins |

Configure scheduler intervals in `hooks.py` or via `bench set-scheduler-events` if needed.

## Accounting Flow

When the HR user clicks **Pay Salary**:

1. **Validation**: Status = Submitted, net > 0, accounting config exists
2. **Accrual Journal Entry**:
   - Debit: Salary Expense Account
   - Credit: Salary Payable Account
3. **Payment Journal Entry**:
   - Debit: Salary Payable Account
   - Credit: Bank or Cash Account (based on payment method)
4. **Status change**: Draft → Submitted → Paid
5. **Linkage**: Both journal entries are stored on the Salary Payment

### Cancellation

When cancelling a paid salary:
1. Payment Journal Entry is cancelled (docstatus 2)
2. Accrual Journal Entry is cancelled (docstatus 2)
3. Salary Payment status → Cancelled with recorded reason
4. All accounting documents are **retained** (not deleted) for audit

### Error Handling

If accounting creation fails:
- Salary Payment status stays **NOT Paid** (remains Submitted)
- Error is logged via `frappe.log_error`
- Admin corrects accounting config
- HR user clicks **Pay** again (idempotent — won't create duplicates)

## Permissions

| Feature | System Manager | HR Manager | HR User |
|---------|:---:|:---:|:---:|
| Employee | RW | RW | R |
| Attendance | RW | RW | RW |
| Salary Payment | RW | RW | Create/Write |
| Bulk Salary | RW | RW | RW |
| Payslip | R | R | R |
| Reports | RW | RW | R |
| HRMS Settings | RW | RW | — |
| Biometric Device | RW | RW | — |

## Custom Fields

Adds to **Employee**:
- `gross_salary` (Currency) — Default gross salary for monthly reference

## API

All whitelisted methods are on the document controllers:

**SalaryPayment** (single):
- `calculate()` — Recalculate attendance + net
- `submit_salary()` — Lock financial values (Draft → Submitted)
- `pay_salary(mode_of_payment)` — Post accounting (Submitted → Paid)
- `cancel_salary(reason)` — Reverse accounting (→ Cancelled)

**BulkSalaryPayment**:
- `generate_salaries()` — Create draft salary rows from employee filters
- `calculate_all()` — Refresh attendance + deductions
- `submit_all()` — Submit all linked salary payments
- `pay_all()` — Enqueue background payment
- `print_all_payslips()` — Enqueue bulk PDF generation

## Upgrading / Migration

After pulling new code from the repository:

```bash
bench --site <site-name> migrate
bench clear-cache
bench restart
```

The `after_migrate` hook in `hooks.py` runs `install.after_install()` on every migration to ensure custom fields and settings are up-to-date.

## Testing

```bash
bench --site <site-name> run-tests --app reckon_hrms_lt
```

Tests include:
- Unit tests for pure calculation functions (no DB required)
- Document-level tests for Salary Payment validation

## Directory Structure

```
reckon_hrms_lt/
├── reckon_hrms_lt/
│   ├── __init__.py
│   ├── hooks.py                 # App configuration
│   ├── install.py               # After-install setup
│   ├── api.py                   # Public API functions
│   ├── utils.py                 # Shared utilities (calculations)
│   ├── doc_events.py            # Duplicate checkin/attendance hooks
│   ├── config/
│   │   └── desktop.py           # Workspace config
│   ├── doctype/
│   │   ├── reckon_hrms_settings/
│   │   ├── biometric_device/
│   │   ├── biometric_sync_log/
│   │   ├── salary_payment/
│   │   ├── bulk_salary_payment/
│   │   ├── bulk_salary_employee/
│   │   ├── salary_allowance/
│   │   ├── salary_bonus/
│   │   └── salary_deduction/
│   ├── biometric/
│   │   ├── adapters/
│   │   │   ├── base.py           # Abstract adapter interface
│   │   │   └── zkteco.py         # ZKTeco adapter (placeholder)
│   │   └── manager.py            # Sync orchestration
│   ├── tasks/
│   │   ├── biometric_sync.py     # Hourly scheduled sync
│   │   ├── auto_attendance.py    # Daily auto attendance
│   │   └── bulk_payslip.py       # Bulk payment + PDF generation
│   ├── reports/
│   │   ├── attendance_report/
│   │   ├── salary_report/
│   │   └── biometric_sync_report/
│   ├── print_format/
│   │   └── reckon_payslip/
│   ├── workspace/
│   │   └── reckon_hrms/
│   ├── number_card/
│   │   ├── active_employees/
│   │   ├── today_present/
│   │   └── unpaid_salaries/
│   └── tests/
│       ├── test_calculation.py
│       └── test_salary_payment.py
├── setup.py
├── requirements.txt
├── patches.txt
├── MANIFEST.in
├── license.txt
└── README.md
```

## Extensibility

The app is designed so these can be added later without breaking changes:
- Overtime
- Loan / Salary Advance
- Tax calculation
- Provident Fund
- Leave management
- Employee self-service (mobile check-in)
- Additional biometric vendors (via the adapter pattern)
- Bank salary file generation

## License

MIT. See `license.txt`.

## Credits

Built for Frappe/ERPNext v16 + Frappe HR v16.
Uses standard Frappe HR Employee, Employee Checkin, and Attendance DocTypes without modification.

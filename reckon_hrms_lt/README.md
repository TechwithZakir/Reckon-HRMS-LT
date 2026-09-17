# Reckon HRMS

A simple, user-friendly HRMS application for Frappe/ERPNext v16.

## Philosophy

> **Simple HR experience + Frappe HR attendance + native ERPNext Accounting**

This app is intended for **HR/admin users** who need a straightforward salary
workflow without understanding Salary Structures, Salary Components, Payroll
Entries, or GL Entries.

## Requirements

- Frappe Framework v16
- ERPNext v16
- Frappe HR v16 (`hrms`)
- Bench CLI

The app declares `required_apps = ["erpnext", "hrms"]`, so Bench validates
these are installed before allowing `install-app`.

## Architecture

```
Frappe HR (used as-is, never modified)
  ├── Employee            (adds a `gross_salary` custom field)
  ├── Employee Checkin    (standard)
  └── Attendance          (standard)

Reckon HRMS
  ├── Reckon HRMS Settings
  ├── Salary Payment          (single employee)
  ├── Bulk Salary Payment     (bulk employee)
  ├── Automated Attendance    (Employee Checkin -> Attendance, daily job)
  └── Payslip Print Format
         ↓
  ERPNext Accounting (Journal Entry + Payment Entry)
```

### Why Journal Entry + Payment Entry instead of Payroll Entry?

ERPNext's Payroll Entry requires a Salary Structure Assignment for every
employee plus configured Salary Components - complexity that contradicts the
"simple" philosophy.

This app posts **native ERPNext accounting directly**:

1. **Accrual** - Journal Entry (Salary Expense Dr / Salary Payable Cr)
2. **Payment** - Journal Entry (Salary Payable Dr / Bank or Cash Cr)

This uses standard ERPNext DocTypes, follows Expense -> Payable -> Bank/Cash,
needs zero payroll configuration, and is fully cancellable with an audit trail.

## Installation

```bash
bench get-app https://github.com/TechwithZakir/Reckon-HRMS-LT
bench --site <site-name> install-app reckon_hrms_lt
bench --site <site-name> migrate
bench --site <site-name> clear-cache
```

## Configuration

Open **Reckon HRMS Settings** and configure:

- **Attendance**: working days (default 30), office start time, late threshold
  (default 15 min), late count for 1-day deduction (default 3), absent/half-day
  deduction multipliers, half-day working hours.
- **Accounting**: Company, Salary Expense Account, Salary Payable Account,
  Default Bank Account, Default Cash Account, Cost Center.

Accounting fields are validated at payment time; a missing configuration fails
the payment with a clear message without marking the salary as paid.

## Features

- **Employee**: standard Frappe HR Employee + `gross_salary` custom field
- **Attendance**: reads standard Frappe HR Attendance; daily job converts
  Employee Checkin records (from a shift or manual entry) into Attendance
- **Salary Payment**: per-employee processing with editable gross, allowances,
  bonuses and deductions; server-side calculation
- **Bulk Salary**: generate/edit/pay many employees at once
- **Accounting**: native Journal Entries posted automatically on "Pay"
- **Payslip**: printable PDF via a Jinja print format
- **Reports**: Attendance, Salary, Employee Attendance, Leave, Late, Salary
  Deduction, Allowance, Historical Salary, Paid Salary
- **Workspace**: Reckon HRMS workspace with shortcuts, number cards and report
  links

## Workflow

```
Employee -> Attendance -> Salary -> Enter Gross -> Add Allowance/Bonus ->
Calculate -> Pay -> Auto Accounting -> Print Payslip
```

## Background Jobs

| Schedule | Job | Purpose |
|----------|-----|---------|
| Daily | `reckon_hrms_lt.tasks.auto_attendance.process_auto_attendance` | Mark attendance from yesterday's check-ins |

## Permissions

| Feature | System Manager | HR Manager | HR User |
|---------|:---:|:---:|:---:|
| Employee | RW | RW | R |
| Attendance | RW | RW | RW |
| Salary Payment | RW | RW | RW |
| Bulk Salary | RW | RW | RW |
| Reports | RW | RW | R |
| Reckon HRMS Settings | RW | RW | — |

The `HR User` role is present in Frappe HR and is created if missing.

## Accounting Flow

On **Pay Salary**:

1. Validate status (Submitted), net > 0, accounting config
2. Accrual Journal Entry - Salary Expense (Dr) / Salary Payable (Cr)
3. Payment Journal Entry - Salary Payable (Dr) / Bank or Cash (Cr)
4. Status -> Paid; both entries are stored on the Salary Payment

On **Cancel**:

1. Payment Journal Entry is cancelled (docstatus 2)
2. Accrual Journal Entry is cancelled
3. Status -> Cancelled with reason; records kept for audit

On **failure** the salary stays unpaid, the error is logged via
`frappe.log_error`, and retrying is idempotent (no duplicate entries).

## Upgrading / Migration

```bash
bench update
bench --site <site-name> migrate
```

`after_migrate` only creates the `gross_salary` custom field and default
settings when missing; it never overwrites administrator changes.

## Development / Testing

```bash
bench start
bench --site <site-name> run-tests --app reckon_hrms_lt
```

Tests cover salary calculation and Salary Payment validation.

## Directory Structure

```
reckon_hrms_lt/
├── reckon_hrms_lt/
│   ├── __init__.py
│   ├── hooks.py
│   ├── install.py
│   ├── api.py
│   ├── utils.py
│   ├── doc_events.py
│   ├── modules.txt            # "Reckon HRMS"
│   ├── config/
│   ├── tasks/
│   │   ├── auto_attendance.py
│   │   └── bulk_payslip.py
│   ├── tests/
│   └── reckon_hrms/           # Frappe module (scrub("Reckon HRMS"))
│       ├── doctype/
│       │   ├── reckon_hrms_settings/
│       │   ├── salary_payment/
│       │   ├── salary_allowance/
│       │   ├── salary_bonus/
│       │   ├── salary_deduction/
│       │   ├── bulk_salary_payment/
│       │   └── bulk_salary_employee/
│       ├── report/
│       ├── workspace/
│       ├── print_format/
│       └── number_card/
├── setup.py
├── requirements.txt
├── MANIFEST.in
├── patches.txt
├── license.txt
└── README.md
```

## License

MIT. Copyright (c) 2026 Reckon Technologies Ltd. — www.reckon.tech — hello@reckon.tech
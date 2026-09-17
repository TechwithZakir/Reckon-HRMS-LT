# Reckon-HRMS-LT

Simple HRMS application for Frappe/ERPNext v16.

**Developed by Reckon Technologies Ltd.**
Website: www.reckon.tech
Email: hello@reckon.tech

## Quick Start

```bash
bench get-app https://github.com/TechwithZakir/Reckon-HRMS-LT
bench --site <site-name> install-app reckon_hrms_lt
bench --site <site-name> migrate
```

See `reckon_hrms_lt/README.md` for full setup and configuration instructions.

## Features

- **Employees**: Standard Frappe HR Employee with `gross_salary` custom field
- **Attendance**: Standard Frappe HR Attendance + Employee Checkin, auto-processed daily
- **Salary Payment**: Simple per-employee processing with editable gross, allowances, bonuses, deductions
- **Bulk Salary**: Process all employees at once with editable columns
- **Accounting**: Native ERPNext Journal Entry + Payment Entry (auto-posted on Pay)
- **Payslip**: Professional printable PDF
- **Reports**: Attendance, Salary, Leave, Late, Deductions, Allowances, Historical, Paid
- **Dashboard**: Reckon HRMS workspace with number cards and analytics

## Core Philosophy

> Simple HR experience + Frappe HR attendance + native ERPNext Accounting

The average HR user should never need to understand Salary Structure, Payroll
Entry, or GL Entry. The complexity remains behind the scenes.

## Requirements

- Frappe Framework v16
- ERPNext v16
- Frappe HR v16 (`hrms`)

## License

MIT License. Copyright (c) 2026 Reckon Technologies Ltd. See `license.txt` for full details.
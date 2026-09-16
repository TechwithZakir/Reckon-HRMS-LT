# Reckon-HRMS-LT

Simple HRMS application for Frappe/ERPNext v16.

**Developed by Reckon Technologies Ltd.**  
Website: www.reckon.tech  
Email: hello@reckon.tech

## Quick Start

See `reckon_hrms_lt/README.md` for installation and usage instructions.

## Features

- **Employees**: Standard Frappe HR Employee with `gross_salary` custom field
- **Attendance**: Standard Frappe HR Attendance + Employee Checkin, auto-processed daily
- **Biometric**: Adapter-based framework (ZKTeco placeholder, extensible for more vendors)
- **Salary Payment**: Simple per-employee processing with editable gross, allowances, bonuses, deductions
- **Bulk Salary**: Process all employees at once with editable columns
- **Accounting**: Native ERPNext Journal Entry + Payment Entry (auto-posted on Pay)
- **Payslip**: Professional printable PDF
- **Reports**: 10+ reports including Attendance, Salary, Leave, Late, Deductions, Allowances
- **Dashboard**: Reckon HRMS workspace with number cards and analytics

## Core Philosophy

> Simple HR experience + Frappe HR attendance + optional biometric + native ERPNext Accounting

The average HR user should never need to understand Salary Structure, Payroll Entry, or GL Entry. The complexity remains behind the scenes.

## License

MIT License. Copyright (c) 2026 Reckon Technologies Ltd. See `license.txt` for full details.

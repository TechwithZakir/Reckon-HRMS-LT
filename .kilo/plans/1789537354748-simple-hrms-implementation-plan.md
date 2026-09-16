# Reckon HRMS Implementation Plan

## Project Overview
- **App Name**: `reckon_hrms_lt`
- **Module Name**: `Reckon HRMS`
- **Target**: Existing Frappe Bench with Frappe/ERPNext v16.x + Frappe HR v16
- **Philosophy**: Simple HR experience + Frappe HR attendance + optional biometric + native ERPNext accounting

---

## Architecture Decisions

| Aspect | Decision |
|--------|----------|
| App Creation | Add to existing bench as installable app |
| Employee | Use Frappe HR `Employee` DocType (add `gross_salary` custom field) |
| Attendance | Use Frappe HR `Employee Checkin` + `Attendance` |
| Salary Processing | Custom `Salary Payment` DocType (single) + `Bulk Salary Payment` |
| Accounting | ERPNext **Payroll Entry → Salary Slip → Journal Entry** (standard flow) |
| Biometric | Adapter framework (ZKTeco implementation deferred) |
| Currency | Multi-currency (per company) |

---

## DocTypes to Create

### 1. Reckon HRMS Settings (Single DocType)
**Purpose**: Central configuration for attendance rules, biometric, accounting

**Fields**:
- **Attendance Settings** (Section Break)
  - `working_days` (Int, default: 30)
  - `late_threshold_minutes` (Int, default: 15)
  - `late_count_for_deduction` (Int, default: 3) - "3 Late = 1 Day"
  - `absent_deduction_per_day` (Float, default: 1)
  - `half_day_deduction` (Float, default: 0.5)
- **Biometric Settings** (Section Break)
  - Child Table: `biometric_devices` → links to `Biometric Device`
- **Accounting Settings** (Section Break)
  - `company` (Link/Company)
  - `salary_expense_account` (Link/Account, filtered by company)
  - `salary_payable_account` (Link/Account, filtered by company)
  - `default_bank_account` (Link/Account)
  - `default_cash_account` (Link/Account)
  - `cost_center` (Link/Cost Center)

---

### 2. Biometric Device
**Purpose**: Configure biometric devices for sync

**Fields**:
- `device_name` (Data, reqd)
- `device_type` (Select: ZKTeco, Generic)
- `ip_address` (Data)
- `port` (Int, default: 4370)
- `username` (Data)
- `password` (Password)
- `sync_interval_minutes` (Int, default: 30)
- `enabled` (Check, default: 1)
- `employee_id_field` (Select: employee_id, user_id, custom) - for mapping
- **Actions**: `Test Connection`, `Sync Now` (buttons)

---

### 3. Biometric Sync Log
**Purpose**: Track sync history

**Fields**:
- `device` (Link/Biometric Device)
- `sync_time` (Datetime, reqd)
- `records_processed` (Int)
- `successful` (Int)
- `failed` (Int)
- `error_message` (Text)
- `status` (Select: Success, Partial, Failed)

---

### 4. Salary Payment (Main DocType)
**Purpose**: Single employee salary processing

**Fields**:
- `employee` (Link/Employee, reqd)
- `salary_month` (Select: Month-Year format, reqd)
- `company` (Link/Company, reqd, fetch from employee)
- **Gross Salary Section**:
  - `gross_salary` (Currency, reqd)
- **Attendance Section** (Read-only, computed):
  - `present_days` (Float)
  - `absent_days` (Float)
  - `late_count` (Int)
  - `half_day_count` (Float)
  - `attendance_deduction` (Currency)
- **Allowances** (Child Table: `salary_allowances`):
  - `allowance_type` (Data)
  - `amount` (Currency)
  - `remarks` (Data)
- **Bonuses** (Child Table: `salary_bonuses`):
  - `bonus_type` (Data)
  - `amount` (Currency)
  - `remarks` (Data)
- **Other Deductions** (Child Table: `salary_deductions`):
  - `deduction_type` (Data)
  - `amount` (Currency)
  - `reason` (Data)
- **Calculation**:
  - `net_salary` (Currency, read-only)
- **Payment**:
  - `payment_method` (Select: Bank, Cash)
  - `bank_account` (Link/Account, depends on payment_method)
  - `payment_date` (Date)
  - `reference_no` (Data)
- **Accounting**:
  - `payroll_entry` (Link/Payroll Entry, read-only)
  - `salary_slips` (Link/Salary Slip, read-only, Table MultiSelect)
  - `journal_entry` (Link/Journal Entry, read-only)
- **Status**:
  - `status` (Select: Draft, Submitted, Paid, Cancelled)
- **Buttons**: `Calculate`, `Save`, `Submit`, `Pay Salary`, `Print Payslip`, `Cancel`

**Validations**:
- Unique: `employee` + `salary_month` + `company`
- `gross_salary` > 0
- `net_salary` >= 0
- Cannot modify if status = Paid

---

### 5. Bulk Salary Payment
**Purpose**: Bulk salary generation and processing

**Fields**:
- `salary_month` (Select, reqd)
- `company` (Link/Company, reqd)
- `department` (Link/Department)
- `employee_type` (Link/Employee Type)
- `grade` (Link/Employee Grade)
- `status` (Select: Draft, Generated, Submitted, Paid, Cancelled)
- **Employees Table** (Child Table: `bulk_salary_employees`):
  - `employee` (Link/Employee)
  - `employee_name` (Data, fetch)
  - `department` (Data, fetch)
  - `gross_salary` (Currency, editable)
  - `allowance_total` (Currency, editable, sum from child)
  - `bonus_total` (Currency, editable, sum from child)
  - `attendance_deduction` (Currency, read-only)
  - `other_deduction_total` (Currency, editable)
  - `net_salary` (Currency, read-only)
  - `salary_payment` (Link/Salary Payment, read-only)
- **Buttons**: `Generate Salaries`, `Calculate All`, `Save All`, `Submit All`, `Pay All`, `Print All Payslips`

---

### 6. Attendance Sheet (Report View)
**Purpose**: Simple daily attendance view for HR

**Not a DocType** - implemented as a **Report** or **Dashboard Chart**

---

## Server-Side Logic

### Salary Calculation (Salary Payment)
```python
def calculate_salary(self):
    # 1. Get working_days from HRMS Settings
    # 2. Get attendance for employee/month
    # 3. Calculate:
    #    daily_salary = gross_salary / working_days
    #    absent_deduction = absent_days * daily_salary * absent_deduction_per_day
    #    late_deduction = (late_count // late_count_for_deduction) * daily_salary
    #    half_day_deduction = half_day_count * daily_salary * half_day_deduction
    #    attendance_deduction = absent_deduction + late_deduction + half_day_deduction
    # 4. allowance_total = sum(allowances)
    # 5. bonus_total = sum(bonuses)
    # 6. other_deduction_total = sum(deductions)
    # 7. net_salary = gross_salary + allowance_total + bonus_total - attendance_deduction - other_deduction_total
```

### Attendance Processing (Background Job)
```python
def process_attendance_for_month(company, month):
    # For each employee in company:
    #   Get checkins for month
    #   Group by date
    #   Determine status per day based on HRMS Settings rules
    #   Create/update Attendance records
    #   Handle late/half-day/absent logic
```

### Biometric Sync (Background Job)
```python
def sync_biometric_device(device):
    # 1. Connect via adapter
    # 2. Fetch new checkins since last sync
    # 3. Map device user_id to Employee
    # 4. Create Employee Checkin records (avoid duplicates)
    # 5. Log results to Biometric Sync Log
```

### Accounting Integration (Pay Salary)
```python
def pay_salary(self):
    # 1. Validate: status == Submitted, accounting config exists
    # 2. Create Payroll Entry:
    #    - company, payroll_frequency="Monthly", start_date, end_date
    # 3. Add employee to Payroll Entry
    # 4. Submit Payroll Entry → creates Salary Slips
    # 5. Submit Salary Slips → creates Journal Entries
    # 6. Make Payment Entry against Salary Payable (Bank/Cash)
    # 7. Link Payroll Entry, Salary Slips, Journal Entry to Salary Payment
    # 8. Set status = Paid
```

---

## Client-Side Scripts

### Salary Payment Form
- **Refresh**: Fetch attendance on employee/month change
- **Calculate Button**: Call `calculate_salary` server method
- **Pay Salary Button**: Call `pay_salary` server method (with confirmation)
- **Allowance/Bonus/Deduction Tables**: Inline editable grid

### Bulk Salary Payment Form
- **Generate Salaries**: Fetch employees matching filters, create rows with gross_salary from Employee
- **Inline Editing**: Gross, Allowance, Bonus, Other Deduction editable
- **Calculate All**: Recalculate all rows
- **Pay All**: Loop through rows, call pay_salary for each (or bulk Payroll Entry)

### Biometric Device Form
- **Test Connection**: Call adapter test method
- **Sync Now**: Enqueue background sync job

---

## Biometric Adapter Architecture

```python
# simple_hrms/biometric/adapters/base.py
class BiometricAdapter:
    def test_connection(self) -> bool
    def fetch_checkins(self, since: datetime) -> List[CheckinRecord]
    def disconnect(self)

# simple_hrms/biometric/adapters/zkteco.py
class ZKTecoAdapter(BiometricAdapter):
    # Implementation using pyZK or zk library (placeholder for now)

# simple_hrms/biometric/manager.py
class BiometricSyncManager:
    def sync_device(self, device: BiometricDevice)
    def sync_all_enabled(self)
```

---

## Background Jobs

| Job | Frequency | Method |
|-----|-----------|--------|
| Biometric Sync | Per device `sync_interval_minutes` | `simple_hrms.tasks.sync_biometric_devices` |
| Auto Attendance | Daily at 02:00 | `simple_hrms.tasks.process_auto_attendance` |
| Bulk Payslip Print | On demand | `simple_hrms.tasks.generate_bulk_payslips` |

---

## Permissions

| Role | Employee | Attendance | Salary Payment | Bulk Salary | Payslip | Reports | Settings |
|------|----------|------------|----------------|-------------|---------|---------|----------|
| HR Manager | RW | RW | RW | RW | R | RW | RW |
| HR User | R | RW | RW | RW | R | R | - |
| System Manager | RW | RW | RW | RW | RW | RW | RW |

**Custom Permissions**:
- Accounting Settings in HRMS Settings: Only System Manager / HR Manager with explicit permission
- `Pay Salary` action: Requires `Salary Payment` submit + Accounting config

---

## Reports

### 1. Attendance Report
- Filters: Date Range, Employee, Department, Status
- Columns: Employee, Date, Check In, Check Out, Working Hours, Status

### 2. Salary Report
- Filters: Month, Employee, Department, Payment Status
- Columns: Employee, Gross, Allowance, Bonus, Attendance Deduction, Other Deduction, Net, Status

### 3. Biometric Sync Report
- Filters: Device, Date Range
- Columns: Device, Sync Time, Records Processed, Successful, Failed, Error

---

## Workspace / Dashboard

**Reckon HRMS Workspace** (Module: `Reckon HRMS`):
```
Reckon HRMS
├── Employees (Frappe HR Employee)
├── Attendance (Attendance Sheet Report)
├── Salary (Salary Payment List)
├── Bulk Salary (Bulk Salary Payment List)
├── Payslips (Salary Payment with Print)
├── Reports
│   ├── Attendance Report
│   ├── Salary Report
│   └── Biometric Sync Report
└── Settings (Reckon HRMS Settings)
```

**Dashboard Cards**:
- Total Employees
- Today: Present / Absent / Late
- Current Month: Gross / Net / Paid / Unpaid

---

## Print Formats

### Payslip (Standard)
- Company Logo, Name, Address
- Employee: Name, ID, Department, Designation
- Salary Month
- Earnings: Gross, Allowances, Bonuses
- Deductions: Attendance, Other
- Net Salary (prominent)
- Payment Status, Date, Method
- Authorized Signatory

### Bulk Payslip
- Combined PDF with page break per employee

---

## Installation & Migration

### Installation
```bash
bench get-app reckon_hrms_lt <repo-url>
bench install-app reckon_hrms_lt
bench migrate
```

### Post-Install Setup
1. Run `Reckon HRMS Setup Wizard` (optional) to configure:
   - Attendance rules
   - Accounting accounts per company
   - Biometric devices (if any)

### Upgrade/Migration
- Use `after_migrate` hooks for schema changes
- Version-specific patches in `patches.txt`

---

## Testing Strategy

### Unit Tests
- Salary calculation logic (various attendance scenarios)
- Attendance processing rules
- Biometric adapter interface
- Accounting integration (mock ERPNext)

### Integration Tests
- Full salary flow: Create → Calculate → Submit → Pay → Verify Journal Entry
- Biometric sync: Create device → Sync → Verify Checkins → Verify Attendance
- Bulk salary: Generate → Edit → Pay All → Verify all paid

### Test Data
- Fixtures: HRMS Settings, Sample Biometric Device, Test Employees

---

## File Structure

```
reckon_hrms_lt/
├── reckon_hrms_lt/
│   ├── __init__.py
│   ├── config/
│   │   ├── desktop.py          # Workspace
│   │   └── hooks.py            # App hooks
│   ├── doctype/
│   │   ├── reckon_hrms_settings/
│   │   ├── biometric_device/
│   │   ├── biometric_sync_log/
│   │   ├── salary_payment/
│   │   │   ├── salary_payment.py
│   │   │   ├── salary_payment.js
│   │   │   └── salary_payment.json
│   │   └── bulk_salary_payment/
│   ├── biometric/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── zkteco.py       # Placeholder
│   │   └── manager.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── biometric_sync.py
│   │   ├── auto_attendance.py
│   │   └── bulk_payslip.py
│   ├── reports/
│   │   ├── attendance_report/
│   │   ├── salary_report/
│   │   └── biometric_sync_report/
│   ├── print_formats/
│   │   └── payslip.html
│   ├── api.py                  # Public APIs
│   └── utils.py                # Shared utilities
├── patches.txt
├── requirements.txt
├── setup.py
└── README.md
```

---

## Implementation Order

1. **App Scaffold** - `bench new-app reckon_hrms_lt`, hooks, permissions
2. **Reckon HRMS Settings** - Single DocType with all config sections
3. **Biometric Framework** - Device, Sync Log, Adapter base, Manager, Background job
4. **Salary Payment** - DocType, calculation, form script, payslip print
5. **Accounting Integration** - Pay Salary → Payroll Entry → Salary Slip → Journal Entry
6. **Bulk Salary Payment** - DocType, generation, bulk actions
6. **Attendance Processing** - Auto attendance background job
7. **Reports** - 3 reports with filters
8. **Workspace & Dashboard** - Desktop cards, charts
9. **Permissions** - Role setup, custom permissions
10. **Tests** - Unit + integration
11. **Documentation** - README, installation guide

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Accounting config missing at pay time | Validate in `pay_salary`, clear error message |
| Duplicate salary for same month | Unique constraint + server validation |
| Biometric sync creates duplicate checkins | Check existing checkin by employee+timestamp |
| Payroll Entry fails silently | Wrap in try/except, log error, don't mark Paid |
| Large bulk payroll times out | Use background job for Pay All, batch processing |

---

## Open Questions (Resolved)

1. ✅ App creation: Existing bench
2. ✅ Version: Frappe/ERPNext v16.x latest
3. ✅ Biometric: Adapter framework only (ZKTeco later)
4. ✅ Accounting: Payroll Entry + Salary Slip (standard ERPNext)
5. ✅ Currency: Multi-currency per company

---

## Next Steps

1. Create app scaffold in existing bench
2. Implement DocTypes in order above
3. Test each component incrementally
4. Verify accounting integration with ERPNext demo data
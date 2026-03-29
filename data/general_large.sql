CREATE TABLE contacts (
  contact_id STRING,
  name STRING,
  email STRING,
  phone STRING,
  alternate_email STRING,
  city STRING,
  state STRING,
  pincode STRING,
  company_name STRING,
  company_website STRING,
  gst_no STRING,
  pan_no STRING,
  department STRING,
  designation STRING,
  linkedin_url STRING,
  date_of_birth DATE,
  blood_group STRING,
  emergency_contact_name STRING,
  emergency_contact_phone STRING,
  notes TEXT
);

CREATE TABLE projects (
  project_id STRING,
  project_name STRING,
  client_name STRING,
  client_contact_name STRING,
  client_phone STRING,
  manager_name STRING,
  team_lead_name STRING,
  start_date DATE,
  deadline DATE,
  completion_date DATE,
  status STRING,
  priority STRING,
  budget DECIMAL(16,2),
  spent_amount DECIMAL(16,2),
  hours_allocated INT,
  hours_spent INT,
  project_type STRING,
  location STRING
);

CREATE TABLE timesheets (
  timesheet_id STRING,
  employee_id STRING,
  employee_name STRING,
  project_id STRING,
  date DATE,
  hours_logged DECIMAL(4,2),
  description TEXT,
  approved_by STRING,
  approved_date DATE,
  billable BOOLEAN
);

CREATE TABLE invoices (
  invoice_id STRING,
  project_id STRING,
  client_name STRING,
  invoice_date DATE,
  due_date DATE,
  amount DECIMAL(12,2),
  tax DECIMAL(12,2),
  total_amount DECIMAL(12,2),
  payment_status STRING,
  payment_date DATE,
  payment_mode STRING,
  utr_no STRING
);

CREATE TABLE assets (
  asset_id STRING,
  asset_tag STRING,
  asset_type STRING,
  assigned_to STRING,
  assigned_date DATE,
  mac_address STRING,
  ip_address STRING,
  serial_no STRING,
  purchase_date DATE,
  warranty_expiry DATE,
  location STRING,
  floor_no INT
);

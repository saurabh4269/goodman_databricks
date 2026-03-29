CREATE TABLE contacts (
  contact_id STRING,
  name STRING,
  email STRING,
  phone STRING,
  city STRING,
  state STRING,
  company_name STRING,
  gst_no STRING,
  department STRING,
  designation STRING,
  linkedin_url STRING,
  notes TEXT
);

CREATE TABLE projects (
  project_id STRING,
  project_name STRING,
  client_name STRING,
  manager_name STRING,
  start_date DATE,
  deadline DATE,
  status STRING,
  budget DECIMAL(14,2),
  hours_allocated INT
);

CREATE TABLE timesheets (
  employee_id STRING,
  project_id STRING,
  date DATE,
  hours_logged DECIMAL(4,2),
  description TEXT,
  approved_by STRING
);

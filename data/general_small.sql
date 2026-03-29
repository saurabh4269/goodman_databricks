CREATE TABLE contacts (
  name STRING,
  email STRING,
  phone STRING,
  department STRING,
  role STRING,
  employee_id STRING
);

CREATE TABLE projects (
  project_id STRING,
  project_name STRING,
  manager_id STRING,
  client_name STRING,
  budget DECIMAL(12,2),
  start_date DATE,
  end_date DATE
);

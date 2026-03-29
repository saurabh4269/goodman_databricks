CREATE TABLE employees (
  emp_id STRING,
  full_name STRING,
  email STRING,
  phone STRING,
  department STRING,
  designation STRING,
  date_of_birth DATE,
  date_of_joining DATE,
  status STRING
);

CREATE TABLE salary (
  salary_id STRING,
  emp_id STRING,
  basic_salary DECIMAL(10,2),
  hra DECIMAL(8,2),
  bank_ac_no STRING,
  ifsc_code STRING,
  month INT,
  year INT,
  payment_date DATE
);

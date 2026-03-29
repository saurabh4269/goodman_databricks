CREATE TABLE subscribers (
  subscriber_id STRING,
  full_name STRING,
  phone STRING,
  email STRING,
  address STRING,
  aadhaar_no STRING,
  plan_name STRING,
  activation_date DATE,
  status STRING
);

CREATE TABLE cdr (
  call_id STRING,
  subscriber_id STRING,
  called_number STRING,
  call_type STRING,
  duration_seconds INT,
  timestamp TIMESTAMP
);

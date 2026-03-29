CREATE TABLE subscribers (
  subscriber_id STRING,
  full_name STRING,
  phone STRING,
  alternate_phone STRING,
  email STRING,
  address STRING,
  city STRING,
  state STRING,
  pincode STRING,
  aadhaar_no STRING,
  alternate_id_type STRING,
  alternate_id_no STRING,
  sim_no STRING,
  imsi STRING,
  plan_name STRING,
  plan_type STRING,
  monthly_rental DECIMAL(8,2),
  data_limit_gb INT,
  activation_date DATE,
  port_in_date DATE,
  port_out_date DATE,
  status STRING
);

CREATE TABLE cdr (
  call_id STRING,
  subscriber_id STRING,
  called_number STRING,
  calling_number STRING,
  call_type STRING,
  call_direction STRING,
  duration_seconds INT,
  duration_minutes DECIMAL(6,2),
  timestamp TIMESTAMP,
  tower_location STRING,
  cell_id STRING,
  lac STRING,
  imei STRING,
  status STRING,
  roam_indicator BOOLEAN
);

CREATE TABLE recharge_history (
  recharge_id STRING,
  subscriber_id STRING,
  amount DECIMAL(8,2),
  plan_name STRING,
  validity_days INT,
  data_offered_gb INT,
  recharge_date TIMESTAMP,
  payment_mode STRING,
  operator_txn_id STRING,
  status STRING
);

CREATE TABLE support_tickets (
  ticket_id STRING,
  subscriber_id STRING,
  phone STRING,
  issue_type STRING,
  issue_description TEXT,
  status STRING,
  assigned_to STRING,
  resolution TEXT,
  created_at TIMESTAMP,
  resolved_at TIMESTAMP
);

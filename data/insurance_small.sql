CREATE TABLE policyholders (
  holder_id STRING,
  full_name STRING,
  phone STRING,
  email STRING,
  date_of_birth DATE,
  nominee_name STRING,
  policy_no STRING,
  policy_type STRING,
  sum_insured DECIMAL(12,2),
  premium DECIMAL(10,2),
  policy_start_date DATE,
  policy_end_date DATE,
  status STRING
);

CREATE TABLE claims (
  claim_id STRING,
  holder_id STRING,
  policy_no STRING,
  claim_type STRING,
  claim_amount DECIMAL(10,2),
  approved_amount DECIMAL(10,2),
  status STRING,
  claim_date DATE
);

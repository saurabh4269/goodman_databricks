CREATE TABLE customers (
  customer_id STRING,
  full_name STRING,
  phone_no STRING,
  email STRING,
  aadhaar_no STRING,
  pan_no STRING,
  account_no STRING,
  ifsc_code STRING,
  kyc_status STRING,
  kyc_verified_at TIMESTAMP
);

CREATE TABLE transactions (
  txn_id STRING,
  customer_id STRING,
  amount DECIMAL(12,2),
  txn_type STRING,
  upi_handle STRING,
  merchant_name STRING,
  utr_no STRING,
  status STRING,
  created_at TIMESTAMP
);

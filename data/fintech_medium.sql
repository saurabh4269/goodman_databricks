CREATE TABLE customers (
  customer_id STRING,
  full_name STRING,
  phone_no STRING,
  email STRING,
  aadhaar_no STRING,
  pan_no STRING,
  voter_id STRING,
  account_no STRING,
  ifsc_code STRING,
  bank_name STRING,
  branch_name STRING,
  kyc_status STRING,
  kyc_verified_by STRING,
  kyc_verified_at TIMESTAMP,
  risk_score INT,
  risk_category STRING
);

CREATE TABLE transactions (
  txn_id STRING,
  customer_id STRING,
  amount DECIMAL(12,2),
  currency STRING,
  txn_type STRING,
  txn_mode STRING,
  upi_handle STRING,
  merchant_id STRING,
  merchant_name STRING,
  merchant_category STRING,
  utr_no STRING,
  narration STRING,
  status STRING,
  created_at TIMESTAMP,
  completed_at TIMESTAMP
);

CREATE TABLE cards (
  card_id STRING,
  customer_id STRING,
  card_last4 STRING,
  card_type STRING,
  expiry_month INT,
  expiry_year INT,
  card_issuer STRING,
  card_network STRING,
  card_status STRING,
  issued_at TIMESTAMP
);

CREATE TABLE addresses (
  address_id STRING,
  customer_id STRING,
  address_type STRING,
  street_address STRING,
  city STRING,
  state STRING,
  pincode STRING,
  landmark STRING,
  latitude DECIMAL(9,6),
  longitude DECIMAL(9,6),
  is_verified BOOLEAN
);

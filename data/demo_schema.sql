CREATE TABLE customers (
  customer_id STRING,
  full_name STRING,
  mobile_number STRING,
  email STRING,
  date_of_birth DATE,
  aadhaar_no STRING,
  pan_number STRING,
  guardian_name STRING
);

CREATE TABLE transactions (
  transaction_id STRING,
  customer_id STRING,
  upi_handle STRING,
  utr_number STRING,
  transaction_amount DECIMAL(10,2),
  transaction_timestamp TIMESTAMP
);

CREATE TABLE medical_consultations (
  consultation_id STRING,
  customer_id STRING,
  diagnosis STRING,
  prescription STRING,
  doctor_notes STRING
);

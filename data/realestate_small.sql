CREATE TABLE tenants (
  tenant_id STRING,
  full_name STRING,
  phone STRING,
  email STRING,
  property_address STRING,
  monthly_rent DECIMAL(8,2),
  lease_start_date DATE,
  lease_end_date DATE,
  security_deposit DECIMAL(10,2),
  status STRING
);

CREATE TABLE payments (
  payment_id STRING,
  tenant_id STRING,
  amount DECIMAL(8,2),
  payment_date DATE,
  payment_mode STRING,
  reference_no STRING,
  status STRING
);

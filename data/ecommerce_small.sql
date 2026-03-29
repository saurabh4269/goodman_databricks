CREATE TABLE customers (
  customer_id STRING,
  full_name STRING,
  email STRING,
  phone STRING,
  city STRING,
  state STRING,
  pincode STRING,
  registered_at TIMESTAMP
);

CREATE TABLE orders (
  order_id STRING,
  customer_id STRING,
  product_name STRING,
  quantity INT,
  price DECIMAL(10,2),
  payment_mode STRING,
  order_status STRING,
  order_date TIMESTAMP
);

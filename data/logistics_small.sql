CREATE TABLE shipments (
  shipment_id STRING,
  shipper_name STRING,
  shipper_phone STRING,
  receiver_name STRING,
  receiver_phone STRING,
  origin_city STRING,
  destination_city STRING,
  weight_kg DECIMAL(8,2),
  shipment_date DATE,
  status STRING
);

CREATE TABLE deliveries (
  delivery_id STRING,
  shipment_id STRING,
  driver_name STRING,
  driver_phone STRING,
  vehicle_no STRING,
  delivery_date DATE,
  delivery_status STRING
);

CREATE TABLE users (
  user_id STRING,
  full_name STRING,
  email STRING,
  phone STRING,
  city STRING,
  subscribed BOOLEAN
);

CREATE TABLE content (
  content_id STRING,
  title STRING,
  author_name STRING,
  content_type STRING,
  views INT,
  likes INT
);

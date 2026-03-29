CREATE TABLE users (
  user_id STRING,
  full_name STRING,
  email STRING,
  phone STRING,
  city STRING,
  state STRING,
  date_of_birth DATE,
  gender STRING,
  interests TEXT,
  referral_code STRING,
  subscribed BOOLEAN,
  plan_type STRING,
  subscribed_at TIMESTAMP,
  last_login_at TIMESTAMP,
  login_device STRING
);

CREATE TABLE content (
  content_id STRING,
  title STRING,
  author_name STRING,
  author_id STRING,
  content_type STRING,
  category STRING,
  tags TEXT,
  views INT,
  likes INT,
  shares INT,
  comments_count INT,
  avg_watch_time_seconds INT,
  published_at TIMESTAMP,
  language STRING,
  region_restricted STRING
);

CREATE TABLE subscriptions (
  subscription_id STRING,
  user_id STRING,
  plan_type STRING,
  amount DECIMAL(8,2),
  payment_mode STRING,
  start_date DATE,
  end_date DATE,
  auto_renew BOOLEAN,
  status STRING
);

CREATE TABLE engagement (
  engagement_id STRING,
  user_id STRING,
  content_id STRING,
  watch_time_seconds INT,
  completion_percent INT,
  liked BOOLEAN,
  shared BOOLEAN,
  comment TEXT,
  rated INT,
  created_at TIMESTAMP
);

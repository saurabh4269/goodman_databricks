CREATE TABLE students (
  student_id STRING,
  full_name STRING,
  first_name STRING,
  last_name STRING,
  email STRING,
  phone STRING,
  date_of_birth DATE,
  age INT,
  gender STRING,
  classroom STRING,
  section STRING,
  roll_no STRING,
  guardian_name STRING,
  guardian_phone STRING,
  guardian_relation STRING,
  guardian_email STRING,
  guardian_occupation STRING,
  annual_income DECIMAL(10,2),
  address STRING,
  city STRING,
  state STRING,
  pincode STRING,
  enrollment_date DATE,
  enrollment_status STRING,
  batch STRING,
  medium_of_instruction STRING
);

CREATE TABLE enrollments (
  enrollment_id STRING,
  student_id STRING,
  course_name STRING,
  course_code STRING,
  instructor_name STRING,
  enrollment_date DATE,
  completion_date DATE,
  progress_percent INT,
  status STRING,
  certificate_issued BOOLEAN
);

CREATE TABLE assessments (
  assessment_id STRING,
  student_id STRING,
  course_name STRING,
  assessment_type STRING,
  max_marks INT,
  marks_obtained INT,
  percentage DECIMAL(5,2),
  grade STRING,
  classroom STRING,
  exam_date DATE,
  graded_by STRING,
  feedback TEXT
);

CREATE TABLE attendance (
  attendance_id STRING,
  student_id STRING,
  classroom STRING,
  session_date DATE,
  status STRING,
  marked_by STRING,
  marked_at TIMESTAMP
);

CREATE TABLE students (
  student_id STRING,
  full_name STRING,
  first_name STRING,
  last_name STRING,
  email STRING,
  alternate_email STRING,
  phone STRING,
  alternate_phone STRING,
  date_of_birth DATE,
  age INT,
  gender STRING,
  nationality STRING,
  aadhaar_no STRING,
  passport_no STRING,
  classroom STRING,
  section STRING,
  roll_no STRING,
  stream STRING,
  medium_of_instruction STRING,
  guardian_name STRING,
  guardian_phone STRING,
  guardian_relation STRING,
  guardian_email STRING,
  guardian_occupation STRING,
  guardian_employer STRING,
  guardian_annual_income DECIMAL(10,2),
  second_guardian_name STRING,
  second_guardian_phone STRING,
  address STRING,
  city STRING,
  district STRING,
  state STRING,
  pincode STRING,
  school_name STRING,
  board STRING,
  previous_school STRING,
  enrollment_date DATE,
  enrollment_status STRING,
  batch STRING,
  scholarship_recipient BOOLEAN,
  scholarship_type STRING,
  scholarship_amount DECIMAL(10,2)
);

CREATE TABLE enrollments (
  enrollment_id STRING,
  student_id STRING,
  course_name STRING,
  course_code STRING,
  course_category STRING,
  instructor_name STRING,
  instructor_email STRING,
  enrollment_date DATE,
  completion_date DATE,
  progress_percent INT,
  total_duration_hours INT,
  completed_hours INT,
  status STRING,
  certificate_issued BOOLEAN,
  certificate_no STRING,
  certificate_issue_date DATE,
  refund_status STRING,
  refund_amount DECIMAL(8,2)
);

CREATE TABLE assessments (
  assessment_id STRING,
  student_id STRING,
  course_name STRING,
  assessment_name STRING,
  assessment_type STRING,
  max_marks INT,
  marks_obtained INT,
  percentage DECIMAL(5,2),
  grade STRING,
  rank INT,
  classroom STRING,
  exam_date DATE,
  duration_minutes INT,
  attempted BOOLEAN,
  time_taken_minutes INT,
  graded_by STRING,
  graded_at TIMESTAMP,
  feedback TEXT,
  improvement_areas TEXT
);

CREATE TABLE assignments (
  assignment_id STRING,
  student_id STRING,
  course_name STRING,
  assignment_title STRING,
  submission_date DATE,
  submitted_at TIMESTAMP,
  marks_obtained INT,
  max_marks INT,
  feedback TEXT,
  plagiarism_score DECIMAL(5,2),
  graded_by STRING,
  graded_at TIMESTAMP
);

CREATE TABLE attendance (
  attendance_id STRING,
  student_id STRING,
  course_name STRING,
  classroom STRING,
  session_date DATE,
  session_start_time STRING,
  session_end_time STRING,
  status STRING,
  leave_type STRING,
  leave_approved_by STRING,
  marked_by STRING,
  marked_at TIMESTAMP
);

CREATE TABLE live_sessions (
  session_id STRING,
  student_id STRING,
  course_name STRING,
  instructor_name STRING,
  session_topic STRING,
  session_date DATE,
  join_time TIMESTAMP,
  leave_time TIMESTAMP,
  duration_minutes INT,
  screen_share_time INT,
  chat_messages INT,
  questions_asked INT,
  recording_link STRING
);

CREATE TABLE certificates (
  certificate_id STRING,
  student_id STRING,
  course_name STRING,
  certificate_no STRING,
  issue_date DATE,
  issuer_name STRING,
  grade STRING,
  verification_link STRING,
  validity_date DATE
);

CREATE TABLE placements (
  placement_id STRING,
  student_id STRING,
  company_name STRING,
  job_role STRING,
  ctc DECIMAL(12,2),
  location STRING,
  offer_date DATE,
  joining_date DATE,
  offer_letter_no STRING,
  status STRING,
  placed_by STRING
);

CREATE TABLE patients (
  patient_id STRING,
  full_name STRING,
  first_name STRING,
  last_name STRING,
  phone_no STRING,
  alternate_phone STRING,
  email STRING,
  date_of_birth DATE,
  age INT,
  gender STRING,
  blood_group STRING,
  marital_status STRING,
  occupation STRING,
  emergency_contact_name STRING,
  emergency_contact_phone STRING,
  emergency_contact_relation STRING,
  insurance_id STRING,
  insurer_name STRING,
  policy_no STRING,
  allergies TEXT,
  comorbidities TEXT,
  height_cm DECIMAL(5,2),
  weight_kg DECIMAL(5,2),
  blood_pressure_systolic INT,
  blood_pressure_diastolic INT,
  pulse_rate INT
);

CREATE TABLE consultations (
  consultation_id STRING,
  patient_id STRING,
  doctor_name STRING,
  doctor_registration_no STRING,
  specialization STRING,
  hospital_name STRING,
  hospital_address STRING,
  diagnosis TEXT,
  icd_code STRING,
  prescription TEXT,
  investigation_notes TEXT,
  consultation_type STRING,
  consultation_date TIMESTAMP,
  follow_up_date DATE,
  consultation_fee DECIMAL(8,2),
  payment_mode STRING,
  prescription_generated BOOLEAN
);

CREATE TABLE prescriptions (
  prescription_id STRING,
  consultation_id STRING,
  patient_id STRING,
  medicine_name STRING,
  dosage STRING,
  frequency STRING,
  duration_days INT,
  instructions TEXT,
  prescribed_by STRING,
  pharmacy_name STRING,
  pharmacy_address STRING,
  created_at TIMESTAMP
);

CREATE TABLE lab_reports (
  report_id STRING,
  patient_id STRING,
  consultation_id STRING,
  test_name STRING,
  test_category STRING,
  result_value STRING,
  unit STRING,
  reference_range STRING,
  is_abnormal BOOLEAN,
  report_date TIMESTAMP,
  lab_name STRING,
  lab_address STRING,
  pathologist_name STRING
);

CREATE TABLE patients (
  patient_id STRING,
  full_name STRING,
  phone_no STRING,
  email STRING,
  date_of_birth DATE,
  gender STRING,
  blood_group STRING,
  emergency_contact_name STRING,
  emergency_contact_phone STRING,
  blood_pressure STRING,
  allergies TEXT
);

CREATE TABLE consultations (
  consultation_id STRING,
  patient_id STRING,
  doctor_name STRING,
  diagnosis TEXT,
  prescription TEXT,
  consultation_date TIMESTAMP,
  follow_up_date DATE,
  hospital_name STRING,
  consultation_fee DECIMAL(8,2)
);

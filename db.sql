CREATE DATABASE melanoma_reports_db;

CREATE TABLE MelanomaReport (
    id INT AUTO_INCREMENT PRIMARY KEY, -- Unique ID for each report
    report_id VARCHAR(50) NOT NULL,    -- Report ID
    patient_name VARCHAR(100) NOT NULL, -- Patient Name
    sex ENUM('male', 'female') NOT NULL, -- Patient's Sex
    age FLOAT NOT NULL,                 -- Normalized age value
    anatom_site_general_challenge ENUM(
        'upper extremity',
        'lower extremity',
        'head/neck',
        'torso',
        'unknown',
        'palms/soles',
        'oral/genital'
    ) NOT NULL,                         -- Anatomical site
    diagnosis ENUM(
        'lentigo NOS',
        'lichenoid keratosis',
        'melanoma',
        'nevus',
        'seborrheic keratosis',
        'unknown'
    ) NOT NULL,                         -- Diagnosis type
    date DATE NOT NULL,                 -- Date of the report
    feedback TEXT,                      -- Feedback provided
    image_path VARCHAR(255) NOT NULL,  -- Path to the uploaded image
    predicted_type ENUM('Benign', 'Malignant'), -- Predicted result
    accuracy FLOAT,                     -- Prediction accuracy
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Record creation timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP -- Record last update timestamp
);

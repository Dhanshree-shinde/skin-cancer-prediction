from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os
import uuid
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Configure MySQL database using .env variables
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_DB = os.getenv('MYSQL_DB')

# Establish a connection to the MySQL database
def get_db_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

# Load the pre-trained model
model = load_model("model.keras")

# Create upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Get form data
    report_id = request.form['reportId']
    patient_name = request.form['patientName']
    date = request.form['date']
    sex = request.form['sex']
    age = int(request.form['age'])
    feedback = request.form['feedback']
    anatom_site = request.form['anatom_site_general_challenge']
    diagnosis = request.form['diagnosis']
    file = request.files['inputImage']

    # Save the uploaded image locally
    filename = str(uuid.uuid4()) + "_" + file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    print(f"Received report:")
    print(f"Report ID: {report_id}")
    print(f"Patient Name: {patient_name}")
    print(f"Date: {date}")
    print(f"Sex: {sex}")
    print(f"Age: {age}")
    print(f"Feedback: {feedback}")
    print(f"Anatomical Site: {anatom_site}")
    print(f"Diagnosis: {diagnosis}")
    print(f"Image Path: {filepath}")

    # Insert initial data into the database
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO MelanomaReport (
                report_id, 
                patient_name, 
                sex, 
                age, 
                anatom_site_general_challenge, 
                diagnosis, 
                date, 
                feedback, 
                image_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                report_id, 
                patient_name, 
                sex, 
                age,
                anatom_site, 
                diagnosis, 
                date, 
                feedback, 
                filepath
            ))
            connection.commit()
            report_db_id = cursor.lastrowid
    finally:
        connection.close()

    # Encode metadata
    encoded_sex = 0 if sex.lower() == "female" else 1
    encoded_age = (age - 10) / 80
    anatom_site_map = {
        "upper extremity": 6,
        "lower extremity": 2,
        "head/neck": 1,
        "torso": 5,
        "unknown": 0,
        "palms/soles": 4,
        "oral/genital": 3,
    }
    encoded_anatom_site = anatom_site_map.get(anatom_site.lower(), 0)

    diagnosis_one_hot = [0] * 6
    diagnosis_map = {
        "lentigo NOS": 0,
        "lichenoid keratosis": 1,
        "melanoma": 2,
        "nevus": 3,
        "seborrheic keratosis": 4,
        "unknown": 5,
    }
    if diagnosis in diagnosis_map:
        diagnosis_one_hot[diagnosis_map[diagnosis]] = 1

    # Combine metadata for prediction
    metadata = [
        encoded_sex,
        encoded_age,
        encoded_anatom_site,
        0,
        *diagnosis_one_hot,
    ]

    # Make predictions using the model
    img = load_img(filepath, target_size=(128, 128))  # Resize as per model input
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0  # Normalize image
    
    print(np.array([metadata]))

    prediction = model.predict((img_array, np.array([metadata])))
    predicted_type = "Malignant" if prediction[0][0] > 0.5 else "Benign"
    accuracy = 0
    if predicted_type == "Malignant":
        accuracy = float(prediction[0][0]) * 100
    else:
        accuracy = (1 - float(prediction[0][0])) * 100

    # Update database with prediction results
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
            UPDATE MelanomaReport
            SET predicted_type = %s, accuracy = %s
            WHERE id = %s
            """
            cursor.execute(sql, (predicted_type, accuracy, report_db_id))
            connection.commit()
    finally:
        connection.close()

    return redirect(url_for('report', report_id=report_db_id))

@app.route('/report/<int:report_id>')
def report(report_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM MelanomaReport WHERE id = %s"
            cursor.execute(sql, (report_id,))
            report = cursor.fetchone()
    finally:
        connection.close()

    if not report:
        return "Report not found!", 404

    return render_template('report.html', report=report)

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
from model_architecture import create_model  # Import model architecture

app = Flask(__name__)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///melanoma_reports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the database model
class MelanomaReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(50), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    predicted_type = db.Column(db.String(50), nullable=True)
    accuracy = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.String(255), nullable=True)
    image_path = db.Column(db.String(255), nullable=False)

# Create model and load weights
model = create_model()
model.load_weights('model_weights')  # Load pre-trained weights

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
    feedback = request.form['feedback']
    file = request.files['inputImage']

    # Save the uploaded image locally
    filename = str(uuid.uuid4()) + "_" + file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Insert initial data into the database
    new_report = MelanomaReport(
        report_id=report_id,
        patient_name=patient_name,
        date=date,
        image_path=filepath,
        feedback=feedback
    )
    db.session.add(new_report)
    db.session.commit()

    # Make predictions using the model
    img = load_img(filepath, target_size=(224, 224))  # Resize as per model input
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0) / 255.0  # Normalize image

    prediction = model.predict(img_array)
    predicted_type = "Melanoma" if prediction[0][0] > 0.5 else "Non-Melanoma"
    accuracy = float(prediction[0][0]) * 100

    # Update database with prediction results
    new_report.predicted_type = predicted_type
    new_report.accuracy = accuracy
    db.session.commit()

    return redirect(url_for('report', report_id=new_report.id))

@app.route('/report/<int:report_id>')
def report(report_id):
    report = MelanomaReport.query.get_or_404(report_id)
    return render_template('report.html', report=report)

if __name__ == '__main__':
    db.create_all()  # Create tables if not exist
    app.run(debug=True)

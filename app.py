from flask import Flask, render_template, redirect, url_for, request, flash, session  # Added session import
from flask_migrate import Migrate
from extensions import db
from forms import PatientForm, DoctorForm, AppointmentForm, EditPatientForm, EditDoctorForm, EditAppointmentForm, LoginForm, RegisterForm
from sqlalchemy.exc import IntegrityError
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

client1 = MongoClient('mongodb+srv://saiyedgulamali:Night0220@healthcare.o0e4e.mongodb.net/?retryWrites=true&w=majority&appName=healthcare')
mongo_db = client1['healthcare']  
prescriptions_collection = mongo_db['prescriptions']

def get_prescriptions():
    # Connect to MongoDB
    client = MongoClient('client1')
    db = client.your_database_name
    prescriptions_collection = db.prescriptions  

    prescriptions = prescriptions_collection.find()

    prescription_list = []
    for prescription in prescriptions:
        prescription_list.append({
            'medication': prescription.get('medication'),
            'dosage': prescription.get('dosage'),
            'instructions': prescription.get('instructions'),
            'doctor_id': prescription.get('doctor_id'),
            'created_at': prescription.get('created_at')
        })

    return prescription_list

def create_prescription(doctor_id, patient_id, medication, dosage, instructions):
    prescription = {
        "doctor_id": doctor_id,
        "patient_id": patient_id,
        "medication": medication,
        "dosage": dosage,
        "instructions": instructions,
        "created_at": datetime.now()
    }
    prescriptions_collection.insert_one(prescription)


from models import User, Patient, Doctor, Appointment

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_role', None) 
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if current_user.role not in ['admin', 'doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    form = PatientForm()
    if form.validate_on_submit():
        patient = Patient(name=form.name.data, contact=form.contact.data, medical_history=form.medical_history.data, user_id=current_user.id)
        db.session.add(patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients'))
    patients = Patient.query.all()
    return render_template('patients.html', form=form, patients=patients)

@app.route('/patient/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    if current_user.role not in ['admin', 'doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    patient = Patient.query.get_or_404(id)
    form = EditPatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('patients'))
    return render_template('edit_patient.html', form=form, patient=patient)

@app.route('/patient/delete/<int:id>', methods=['POST'])
@login_required
def delete_patient(id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    patient = Patient.query.get_or_404(id)
    db.session.delete(patient)
    db.session.commit()
    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('patients'))

@app.route('/doctors', methods=['GET', 'POST'])
@login_required
def doctors():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    form = DoctorForm()
    if form.validate_on_submit():
        doctor = Doctor(name=form.name.data, specialization=form.specialization.data, schedule=form.schedule.data, user_id=current_user.id)
        db.session.add(doctor)
        db.session.commit()
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('doctors'))
    doctors = Doctor.query.all()
    return render_template('doctors.html', form=form, doctors=doctors)

@app.route('/doctor/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    doctor = Doctor.query.get_or_404(id)
    form = EditDoctorForm(obj=doctor)
    if form.validate_on_submit():
        form.populate_obj(doctor)
        db.session.commit()
        flash('Doctor updated successfully!', 'success')
        return redirect(url_for('doctors'))
    return render_template('edit_doctor.html', form=form, doctor=doctor)

@app.route('/doctor/delete/<int:id>', methods=['POST'])
@login_required
def delete_doctor(id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    doctor = Doctor.query.get_or_404(id)
    db.session.delete(doctor)
    db.session.commit()
    flash('Doctor deleted successfully!', 'success')
    return redirect(url_for('doctors'))

@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    form = AppointmentForm()
    if form.validate_on_submit():
        try:
            appointment = Appointment(patient_id=form.patient_id.data, 
                                      doctor_id=form.doctor_id.data, 
                                      date=form.date.data, 
                                      time=form.time.data)
            db.session.add(appointment)
            db.session.commit()
            flash('Appointment scheduled successfully!', 'success')
            return redirect(url_for('appointments'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Invalid patient or doctor ID. Please check and try again.', 'error')
    appointments = Appointment.query.all()
    return render_template('appointments.html', form=form, appointments=appointments)

@app.route('/appointment/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_appointment(id):
    if current_user.role not in ['admin', 'doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    appointment = Appointment.query.get_or_404(id)
    form = EditAppointmentForm(obj=appointment)
    if form.validate_on_submit():
        form.populate_obj(appointment)
        db.session.commit()
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('appointments'))
    return render_template('edit_appointment.html', form=form, appointment=appointment)

@app.route('/appointment/delete/<int:id>', methods=['POST'])
@login_required
def delete_appointment(id):
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    appointment = Appointment.query.get_or_404(id)
    db.session.delete(appointment)
    db.session.commit()
    flash('Appointment deleted successfully!', 'success')
    return redirect(url_for('appointments'))

@app.route('/prescription/add', methods=['GET', 'POST'])
@login_required
def add_prescription():
    if current_user.role not in ['doctor', 'admin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        doctor_id = current_user.id
        patient_id = request.form.get('patient_id')
        medication = request.form.get('medication')
        dosage = request.form.get('dosage')
        instructions = request.form.get('instructions')

        create_prescription(doctor_id, patient_id, medication, dosage, instructions)

        flash('Prescription added successfully!', 'success')
        return redirect(url_for('add_prescription'))

    patients = Patient.query.all()
    
    prescriptions = list(prescriptions_collection.find())

    return render_template('add_prescription.html', patients=patients, prescriptions=prescriptions)

@app.route('/prescription/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_prescription(id):
    prescription = prescriptions_collection.find_one({'_id': ObjectId(id)})
    if request.method == 'POST':
        updated_prescription = {
            'medication': request.form.get('medication'),
            'dosage': request.form.get('dosage'),
            'instructions': request.form.get('instructions'),
        }
        prescriptions_collection.update_one({'_id': ObjectId(id)}, {'$set': updated_prescription})
        flash('Prescription updated successfully!', 'success')
        return redirect(url_for('add_prescription'))
    return render_template('edit_prescription.html', prescription=prescription)

@app.route('/prescription/delete/<id>', methods=['POST'])
@login_required
def delete_prescription(id):
    prescriptions_collection.delete_one({'_id': ObjectId(id)})
    flash('Prescription deleted successfully!', 'success')
    return redirect(url_for('add_prescription'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)

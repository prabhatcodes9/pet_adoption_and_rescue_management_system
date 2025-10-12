from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import os
from flask import jsonify
import threading
import time

app = Flask(__name__)
app.secret_key = 'my-secret-key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Prabhat%400@127.0.0.1/pet_rescue_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")

class LostPet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pet_name = db.Column(db.String(100), nullable=False)
    pet_type = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    description = db.Column(db.Text)
    last_seen_location = db.Column(db.String(255))
    date_lost = db.Column(db.Date)
    mobile = db.Column(db.String(15))
    gender = db.Column(db.String(10))
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")

class FoundPet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pet_name = db.Column(db.String(100), nullable=True)
    pet_type = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text)
    found_location = db.Column(db.String(255))
    date_found = db.Column(db.DateTime, default=datetime.utcnow)
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    mobile = db.Column(db.String(15))
    gender = db.Column(db.String(10))
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")

class AdoptPet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pet_name = db.Column(db.String(100), nullable=False)
    pet_type = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    description = db.Column(db.Text)
    age = db.Column(db.String(50))
    injury = db.Column(db.String(10))
    mobile = db.Column(db.String(15))
    gender = db.Column(db.String(10))
    location = db.Column(db.String(255))
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")

class AdoptRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('adopt_pet.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    request_date = db.Column(db.Date)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications', lazy=True)

    def is_expired(self):
        """Check if the notification is older than 10 minutes."""
        return datetime.utcnow() > self.timestamp + timedelta(minutes=10)

@app.route('/admin/approve_pet/<int:pet_id>', methods=['POST'])
@login_required
def approve_pet(pet_id):
    if current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    pet = LostPet.query.get_or_404(pet_id)
    pet.is_approved = True
    db.session.commit()

    # Create notification for the pet owner
    notification = Notification(
        user_id=pet.user_id,
        message=f"Your {pet.pet_type} '{pet.pet_name}' request has been approved by admin."
    )
    db.session.add(notification)
    db.session.commit()

    flash("Pet request approved and user notified!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/')
def home():
    return render_template('index.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login')
def login1():
    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        mobile = request.form.get('mobile') or 'N/A'
        email = request.form.get('email')
        address = request.form.get('address') or 'N/A'
        password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')

        user = User(
            name=name,
            mobile=mobile,     
            email=email,
            address=address,   
            password=password
        )
        db.session.add(user)
        db.session.commit()

        flash('Account created Successfully!')
        return redirect(url_for('login'))
    
    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login Successfully!')
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials!')

    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()   # removes current_user
    flash("You have logged out.", "info")
    return redirect(url_for('home'))  # go back to home page (index.html)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role != "user":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    # Delete notifications older than 10 minutes
    now = datetime.utcnow()
    Notification.query.filter(Notification.timestamp < now - timedelta(minutes=10)).delete()
    db.session.commit()

    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()

    return render_template('dashboard.html', user=current_user, unread_count=unread_count, notifications=notifications)

@app.route('/mark_notifications_read', methods=['POST'])
@login_required
def mark_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({"success": True})

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))
    
    lost_count = LostPet.query.count()
    found_count = FoundPet.query.count()  # Placeholder for FoundPet model
    adopt_count = AdoptPet.query.count()  # Placeholder for AdoptPet model

    return render_template('admin_dashboard.html', user=current_user, lost_count=lost_count, found_count=found_count, adopt_count=adopt_count)

@app.route('/admin/get_pets/<pet_type>')
@login_required
def get_pets(pet_type):
    if current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    # Currently, we only have lost pets implemented
    if pet_type == "lost":
        pets = LostPet.query.all()
    elif pet_type == "found":
        pets = FoundPet.query.all()  # Placeholder for FoundPet model
    else:
        return jsonify([])
    pet_data = [{
            "id": pet.id,
            "name": pet.pet_name,
            "breed": pet.breed,
            "description": pet.description,
            "image": pet.image,
            "gender": pet.gender,
            "pet_type": pet.pet_type,
            "date_lost": pet.date_lost.strftime('%Y-%m-%d') if getattr(pet, 'date_lost', None) else None,
            "date_found": pet.date_found.strftime('%Y-%m-%d') if getattr(pet, 'date_found', None) else None,
            "mobile": pet.mobile
        } for pet in pets]
    
    return jsonify(pet_data)
    
    

@app.route('/admin/delete_pet/<int:pet_id>', methods=['POST'])
@login_required
def delete_pet(pet_id):
    if current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    pet = LostPet.query.get_or_404(pet_id)

    # Delete the image file too if it exists
    image_path = os.path.join('static/uploads', pet.image)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.session.delete(pet)
    db.session.commit()

    return redirect(url_for('admin_lost_pets'))

@app.route('/admin/delete_found_pet/<int:pet_id>', methods=['POST'])
@login_required
def delete_found_pet(pet_id):
    if current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    pet = FoundPet.query.get_or_404(pet_id)

    # Delete the image file too if it exists
    image_path = os.path.join('static/uploads', pet.image)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.session.delete(pet)
    db.session.commit()

    flash("Found pet deleted successfully!", "success")
    return redirect(url_for('admin_found_pets'))

@app.route('/admin/delete_adopt_pet/<int:pet_id>', methods=['POST'])
@login_required
def delete_adopt_pet(pet_id):
    if current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    pet = AdoptPet.query.get_or_404(pet_id)

    AdoptRequest.query.filter_by(pet_id=pet.id).delete()

    # Delete the image file too if it exists
    image_path = os.path.join('static/uploads', pet.image)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.session.delete(pet)
    db.session.commit()

    flash("Adoption pet deleted successfully!", "success")
    return redirect(url_for('admin_adopt_pets'))

@app.route('/admin/lost_pets')
@login_required
def admin_lost_pets():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    # Fetch pets by status
    pending_pets = LostPet.query.filter_by(status='pending').order_by(LostPet.id.desc()).all()
    approved_pets = LostPet.query.filter_by(status='approved').order_by(LostPet.id.desc()).all()
    rejected_pets = LostPet.query.filter_by(status='rejected').order_by(LostPet.id.desc()).all()

    # Pass to template
    return render_template(
        'admin_lost.html',
        user=current_user,
        pending_pets=pending_pets,
        approved_pets=approved_pets,
        rejected_pets=rejected_pets,
        pending_count=len(pending_pets),
        approved_count=len(approved_pets),
        rejected_count=len(rejected_pets)
    )


@app.route('/admin/found_pets')
@login_required
def admin_found_pets():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    pending_pets = FoundPet.query.filter_by(status='pending').order_by(FoundPet.id.desc()).all()
    approved_pets = FoundPet.query.filter_by(status='approved').order_by(FoundPet.id.desc()).all()
    rejected_pets = FoundPet.query.filter_by(status='rejected').order_by(FoundPet.id.desc()).all()

    # Pass to template
    return render_template(
        'admin_found.html',
        user=current_user,
        pending_pets=pending_pets,
        approved_pets=approved_pets,
        rejected_pets=rejected_pets,
        pending_count=len(pending_pets),
        approved_count=len(approved_pets),
        rejected_count=len(rejected_pets)
    )

@app.route('/admin/adopt_pets')
@login_required
def admin_adopt_pets():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('user_dashboard'))

    # Fetch all adoption requests along with related pets and users
    requests = db.session.query(
        AdoptRequest,
        AdoptPet.pet_name,
        AdoptPet.pet_type,
        AdoptPet.breed,
        User.name.label('user_name'),
        User.email.label('user_email')
    ).join(AdoptPet, AdoptRequest.pet_id == AdoptPet.id) \
     .join(User, AdoptRequest.user_id == User.id) \
     .order_by(AdoptRequest.id.desc()).all()

    pets = AdoptPet.query.order_by(AdoptPet.id.desc()).all()
    return render_template('admin_adopt.html', requests=requests, user=current_user, pets=pets)

@app.route('/admin/update_lost_status/<int:pet_id>/<string:action>')
@login_required
def update_lost_status(pet_id, action):
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    pet = LostPet.query.get_or_404(pet_id)
    if action == 'approve':
        pet.status = 'approved'
        flash(f"{pet.pet_name} report approved!", "success")

         # ✅ Add notification for the user
        message = f"Your lost pet report '{pet.pet_name}' has been approved !"
        notif = Notification(user_id=pet.user_id, message=message)
        db.session.add(notif)

    elif action == 'reject':
        pet.status = 'rejected'
        flash(f"{pet.pet_name} report rejected.", "warning")

        # ✅ Optional: notify rejection
        message = f"Your lost pet report '{pet.pet_name}' has been rejected."
        notif = Notification(user_id=pet.user_id, message=message)
        db.session.add(notif)
    
    db.session.commit()
    return redirect(url_for('admin_lost_pets'))

@app.route('/admin/update_found_status/<int:pet_id>/<string:action>')
@login_required
def update_found_status(pet_id, action):
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    pet = FoundPet.query.get_or_404(pet_id)

    if action == 'approve':
        pet.status = 'approved'
        flash(f"{pet.pet_name} found report approved!", "success")

        # ✅ Add notification
        message = f"Your found pet report '{pet.pet_name}' has been approved!"
        notif = Notification(user_id=pet.user_id, message=message)
        db.session.add(notif)

    elif action == 'reject':
        pet.status = 'rejected'
        flash(f"{pet.pet_name} found report rejected.", "warning")

        # ✅ Add rejection notification
        message = f"Your found pet report '{pet.pet_name}' has been rejected."
        notif = Notification(user_id=pet.user_id, message=message)
        db.session.add(notif)

    else:
        flash("Invalid action.", "danger")
        return redirect(url_for('admin_found_pets'))

    db.session.commit()
    return redirect(url_for('admin_found_pets'))

@app.route('/admin/update_adopt_status/<int:pet_id>/<string:action>')
@login_required
def update_adopt_status(pet_id, action):
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    pet = AdoptPet.query.get_or_404(pet_id)

    if action == 'approve':
        pet.status = 'approved'
        flash(f"{pet.pet_name} found report approved!", "success")

        # ✅ Add notification
        message = f"Your adoption pet report '{pet.pet_name}' has been approved!"
        notif = Notification(user_id=pet.user_id, message=message)
        db.session.add(notif)

    elif action == 'reject':
        pet.status = 'rejected'
        flash(f"{pet.pet_name} found report rejected.", "warning")

        # ✅ Add rejection notification
        message = f"Your adoption pet report '{pet.pet_name}' has been rejected."
        notif = Notification(user_id=pet.user_id, message=message)
        db.session.add(notif)

    else:
        flash("Invalid action.", "danger")
        return redirect(url_for('admin_adopt_pets'))

    db.session.commit()
    return redirect(url_for('admin_adopt_pets'))

@app.route('/admin/edit_pet/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    if current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    pet = LostPet.query.get_or_404(pet_id)

    # --- For modal data loading (AJAX GET request) ---
    if request.method == 'GET':
        pet_data = {
            "id": pet.id,
            "pet_name": pet.pet_name,
            "pet_type": pet.pet_type,
            "breed": pet.breed,
            "description": pet.description,
            "last_seen_location": pet.last_seen_location,
            "mobile": pet.mobile,
            "gender": pet.gender,
            "date_lost": pet.date_lost.strftime('%Y-%m-%d') if pet.date_lost else "",
            "image": pet.image
        }
        return jsonify(pet_data)

    # --- For updating pet details via AJAX POST ---
    if request.method == 'POST':
        pet.pet_name = request.form.get('pet_name')
        pet.pet_type = request.form.get('pet_type')
        pet.breed = request.form.get('breed')
        pet.description = request.form.get('description')
        pet.last_seen_location = request.form.get('last_seen_location')
        pet.mobile = request.form.get('mobile')
        pet.gender = request.form.get('gender')

        date_lost = request.form.get('date_lost')
        if date_lost:
            from datetime import datetime
            try:
                pet.date_lost = datetime.strptime(date_lost, '%Y-%m-%d')
            except ValueError:
                pass

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = image_file.filename
            image_path = os.path.join('static/uploads', filename)
            image_file.save(image_path)
            pet.image = filename

        db.session.commit()
        return jsonify({"success": True, "message": "Pet updated successfully!"})
    
@app.route('/admin/edit_found_pet/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def edit_found_pet(pet_id):
    if current_user.role != "admin":
        return jsonify({"error": "Access denied"}), 403

    pet = FoundPet.query.get_or_404(pet_id)

    # --- For modal data loading (AJAX GET request) ---
    if request.method == 'GET':
        pet_data = {
            "id": pet.id,
            "pet_name": pet.pet_name,
            "pet_type": pet.pet_type,
            "breed": pet.breed,
            "description": pet.description,
            "found_location": pet.found_location,
            "mobile": pet.mobile,
            "gender": pet.gender,
            "date_found": pet.date_found.strftime('%Y-%m-%d') if pet.date_found else "",
            "image": pet.image
        }
        return jsonify(pet_data)

    # --- For updating pet details via AJAX POST ---
    if request.method == 'POST':
        pet.pet_name = request.form.get('pet_name')
        pet.pet_type = request.form.get('pet_type')
        pet.breed = request.form.get('breed')
        pet.description = request.form.get('description')
        pet.found_location = request.form.get('found_location')
        pet.mobile = request.form.get('mobile')
        pet.gender = request.form.get('gender')

        date_found = request.form.get('date_found')
        if date_found:
            from datetime import datetime
            try:
                pet.date_found = datetime.strptime(date_found, '%Y-%m-%d')
            except ValueError:
                pass

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = image_file.filename
            image_path = os.path.join('static/uploads', filename)
            image_file.save(image_path)
            pet.image = filename

        db.session.commit()
        return jsonify({"success": True, "message": "Pet updated successfully!"})


@app.route('/report_lost', methods=['GET', 'POST'])
@login_required
def report_lost():
    if request.method == 'POST':
        pet_name = request.form.get('pet_name')
        pet_type = request.form.get('pet_type')
        breed = request.form.get('breed')
        description = request.form.get('description')
        last_seen_location = request.form.get('last_seen_location')
        date_lost = request.form.get('date_lost')
        mobile = request.form.get('mobile') or current_user.mobile
        gender = request.form.get('gender')

        image_file = request.files.get('image')
        filename = image_file.filename
        image_file.save(os.path.join('static/uploads', filename))
        

        new_pet = LostPet(
            user_id=current_user.id,
            pet_name=pet_name,
            pet_type=pet_type,
            breed=breed,
            description=description,
            last_seen_location=last_seen_location,
            date_lost=datetime.strptime(date_lost, '%Y-%m-%d') if date_lost else None,
            mobile=mobile,
            gender=gender,
            image=filename,
            status="pending"
        )
        db.session.add(new_pet)
        db.session.commit()

        flash('Lost pet reported successfully!')
        return redirect(url_for('report_lost'))
    
    lost_pets = LostPet.query.filter_by(status='approved').order_by(LostPet.id.desc()).all()
    return render_template('report_lost.html', user=current_user, lost_pets=lost_pets)

@app.route('/report_adopt', methods=['GET', 'POST'])
@login_required
def report_adopt():
    if request.method == 'POST':
        pet_name = request.form.get('pet_name')
        pet_type = request.form.get('pet_type')
        breed = request.form.get('breed')
        description = request.form.get('description')
        age = request.form.get('age')
        injury = request.form.get('injury')
        gender = request.form.get('gender')
        mobile = request.form.get('mobile')
        location = request.form.get('location')
        image = request.files.get('image')

        image_filename = None
        if image:
            image_filename = image.filename
            image.save(os.path.join('static/uploads', image_filename))

        new_pet = AdoptPet(
            user_id=current_user.id,
            pet_name=pet_name,
            pet_type=pet_type,
            breed=breed,
            description=description,
            age=age,
            injury=injury,
            gender=gender,
            mobile=mobile,
            location=location,
            image=image_filename,
            status="pending"
        )

        db.session.add(new_pet)
        db.session.commit()
        flash("Adoption pet reported successfully!", "success")
        return redirect(url_for('report_adopt'))

    adopt_pets = AdoptPet.query.order_by(AdoptPet.id.desc()).all()
    return render_template('report_adopt.html', user=current_user, adopt_pets=adopt_pets)

@app.route('/user/my_lost_requests')
@login_required
def my_lost_requests():
    user_id = current_user.id
    pets = LostPet.query.filter_by(user_id=user_id).all()
    return render_template('my_lost_request.html',user=current_user, pets=pets)

@app.route('/lost_pets')
@login_required
def lost_pets():
    pets = LostPet.query.filter_by(status='approved').all()  # fetch all lost pets, not just current user
    return render_template('lost_pet.html', pets=pets, user=current_user)

@app.route('/report_found', methods=['GET', 'POST'])
@login_required
def report_found():
    if request.method == 'POST':
        pet_name = request.form.get('pet_name')
        pet_type = request.form.get('pet_type')
        breed = request.form.get('breed')
        description = request.form.get('description')
        found_location = request.form.get('found_location')
        date_found = request.form.get('date_found')
        mobile = request.form.get('mobile') or current_user.mobile
        gender = request.form.get('gender')

        image_file = request.files.get('image')
        filename = image_file.filename
        image_file.save(os.path.join('static/uploads', filename))
        

        new_pet = FoundPet(
            user_id=current_user.id,
            pet_name=pet_name,
            pet_type=pet_type,
            breed=breed,
            description=description,
            found_location=found_location,
            date_found=datetime.strptime(date_found, '%Y-%m-%d') if date_found else None,
            mobile=mobile,
            gender=gender,
            image=filename,
            status="pending"
        )
        db.session.add(new_pet)
        db.session.commit()

        flash('Found pet reported successfully!')
        return redirect(url_for('report_found'))
    
    found_pets = FoundPet.query.filter_by(status='approved').order_by(FoundPet.id.desc()).all()
    return render_template('report_found.html', user=current_user, found_pets=found_pets)

@app.route('/user/my_found_requests')
@login_required
def my_found_requests():
    user_id = current_user.id
    pets = FoundPet.query.filter_by(user_id=user_id).all()
    return render_template('my_found_request.html',user=current_user, pets=pets)

@app.route('/found_pets')
@login_required
def found_pets():
    pets = FoundPet.query.filter_by(status='approved').all()
    return render_template('found_pet.html', user=current_user, pets=pets)

@app.route('/adopt_pets')
@login_required
def adopt_pets():
    pets = AdoptPet.query.filter_by(status='approved').all()
    return render_template('adopt_pet.html', user=current_user, pets=pets)

@app.route('/user/my_adopt_requests')
@login_required
def my_adopt_requests():
    user_id = current_user.id
    pets = AdoptPet.query.filter_by(user_id=user_id).all()
    for pet in pets:
        pet.requests = AdoptRequest.query.filter_by(pet_id=pet.id).all()  # ✅ use "requests"
    return render_template('my_adopt_request.html', user=current_user, pets=pets)

@app.route('/adopt_request/<int:pet_id>', methods=['POST'])
@login_required
def adopt_request(pet_id):
    pet = AdoptPet.query.get_or_404(pet_id)

    # Restrict the original finder from adopting their own pet
    if pet.user_id == current_user.id:
        flash("You cannot adopt a pet you reported as found.", "danger")
        return redirect(url_for('report_adopt'))

    # Prevent duplicate requests by the same user for the same pet
    existing_request = AdoptRequest.query.filter_by(user_id=current_user.id, pet_id=pet.id).first()
    if existing_request:
        flash("You have already sent an adoption request for this pet.", "warning")
        return redirect(url_for('report_adopt'))

    # Collect data from the form
    name = request.form.get('name')
    mobile = request.form.get('mobile')
    address = request.form.get('address')
    reason = request.form.get('reason')

    # Create a new adoption request entry
    new_request = AdoptRequest(
        user_id=current_user.id,
        pet_id=pet.id,
        name=name,
        mobile=mobile,
        address=address,
        reason=reason,
        request_date=datetime.utcnow().date(),
        status="pending"
    )

    db.session.add(new_request)
    db.session.commit()

    flash("Your adoption request has been submitted successfully!", "success")
    return redirect(url_for('report_adopt'))

@app.route('/update_request_status/<int:req_id>', methods=['POST'])
@login_required
def update_request_status(req_id):
    status = request.form.get('status')
    req = AdoptRequest.query.get_or_404(req_id)
    pet = AdoptPet.query.get(req.pet_id)

    # Only owner of pet can accept/reject
    if pet.user_id != current_user.id:
        flash("You are not authorized to modify this request.", "danger")
        return redirect(url_for('my_adopt_request'))

    req.status = status
    db.session.commit()
    flash(f"Request has been {status}.", "success")
    return redirect(url_for('my_adopt_requests'))

@app.route('/admin/adopt_requests')
@login_required
def admin_adopt_requests():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    requests = AdoptRequest.query.order_by(AdoptRequest.id.desc()).all()
    return render_template('admin_adopt.html', requests=requests, user=current_user)

@app.route('/admin/update_adopt_request/<int:req_id>/<string:action>', methods=['POST'])
@login_required
def update_adopt_request(req_id, action):
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    req = AdoptRequest.query.get_or_404(req_id)
    pet = AdoptPet.query.get(req.pet_id)

    if action == "approve":
        req.status = "approved"
        pet.status = "adopted"  # ✅ update pet to adopted
        message = f"Your adoption request for '{pet.pet_name}' has been approved!"
        flash(f"Adoption request for {pet.pet_name} approved!", "success")

    elif action == "reject":
        req.status = "rejected"
        message = f"Your adoption request for '{pet.pet_name}' has been rejected."
        flash(f"Adoption request for {pet.pet_name} rejected!", "warning")
    else:
        flash("Invalid action.", "danger")
        return redirect(url_for('admin_adopt'))

    # Create notification for the requester
    notif = Notification(user_id=req.user_id, message=message)
    db.session.add(notif)

    db.session.delete(req)  # Remove request after decision
    db.session.commit()

    return redirect(url_for('admin_adopt'))

@app.route('/update_lost_edit', methods=['POST'])
@login_required
def update_lost_edit():
    pet_id = request.form.get('pet_id')
    pet = LostPet.query.filter_by(id=pet_id, user_id=current_user.id).first()

    if not pet:
        flash("Pet not found or you are not authorized.", "danger")
        return redirect(url_for('my_lost_request'))

    # Update fields
    pet.pet_name = request.form.get('pet_name')
    pet.pet_type = request.form.get('pet_type')
    pet.breed = request.form.get('breed')
    pet.description = request.form.get('description')
    pet.gender = request.form.get('gender')
    pet.date_lost = request.form.get('date_lost')
    pet.last_seen_location = request.form.get('last_seen_location')
    pet.mobile = request.form.get('mobile')

    # Handle image upload if a new file is selected
    image_file = request.files.get('image')
    if image_file and image_file.filename:
        filename = image_file.filename
        image_path = os.path.join('static/uploads', filename)
        image_file.save(image_path)
        pet.image = filename

    # Commit changes
    db.session.commit()
    flash("Pet details updated successfully!", "success")
    return redirect(url_for('my_lost_requests'))

# ----------- Admin User Creation -----------
with app.app_context():
    admin_email = "admin@petrescue.com"
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        hashed_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
        admin_user = User(
            name="Administrator",
            mobile="N/A",
            email=admin_email,
            address="Head Office",
            password=hashed_password,
            role="admin"
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created: admin@petrescue.com / admin123")

def move_found_pets_to_adopt():
    while True:
        with app.app_context():
            now = datetime.utcnow()
            threshold = now - timedelta(days=1)

            old_pets = FoundPet.query.filter(FoundPet.date_reported < threshold, FoundPet.status=='approved').all()

            for pet in old_pets:
                # Move details to AdoptPet
                adopt_pet = AdoptPet(
                    user_id=pet.user_id,  # original reporter (restricted later)
                    pet_name=pet.pet_name or "Unknown",
                    pet_type=pet.pet_type,
                    breed=pet.breed,
                    description=pet.description,
                    age="Unknown",  # default since not in FoundPet
                    injury="No",   # default, can be updated by admin if needed
                    mobile=pet.mobile,
                    gender=pet.gender,
                    location=pet.found_location,
                    image=pet.image,
                    status="pending"
                )

                db.session.add(adopt_pet)
                db.session.delete(pet)  # remove from found pets

            if old_pets:
                db.session.commit()

        time.sleep(60)  # run every 60 seconds


# Start background thread
thread = threading.Thread(target=move_found_pets_to_adopt, daemon=True)
thread.start()
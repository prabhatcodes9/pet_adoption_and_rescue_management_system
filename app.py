from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import os
from flask import jsonify
import threading
import time
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from flask_apscheduler import APScheduler

app = Flask(__name__)
app.secret_key = 'my-secret-key'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'petconnect99@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'riqy pngs rwks xlak'     # Use an App Password (not your Gmail password)
app.config['MAIL_DEFAULT_SENDER'] = ('PetConnect', 'petconnect99@gmail.com')

schedular = APScheduler()

mail = Mail(app)

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
    pet_status = db.Column(db.String(20), default="lost")
    founded_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='lost_pets')

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
    pet_status = db.Column(db.String(20), default="found")
    founded_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='found_pets')
    adopt_pets = db.relationship('AdoptPet', backref='found_pet', lazy=True)

class AdoptPet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('found_pet.id', ondelete='SET NULL'), nullable=True)
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

class FoundRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('lost_pet.id'), nullable=False)
    finder_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)

    pet = db.relationship('LostPet', backref='found_requests')

class ClaimRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('found_pet.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)

    pet = db.relationship('FoundPet', backref='claim_requests')
    user = db.relationship('User', backref='claim_requests')

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
    
class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('lost_pet.id'), nullable=False)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #Pet owner
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #Finder
    found_request_id = db.Column(db.Integer, db.ForeignKey('found_request.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=False)

class FoundChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('found_pet.id'), nullable=False)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #Pet owner
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #Claimer
    claim_request_id = db.Column(db.Integer, db.ForeignKey('claim_request.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=False)


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class FoundChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('found_chat_room.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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
        return redirect(url_for('home'))
    
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
                return redirect(url_for('admin_home'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials!')

    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()   # removes current_user
    flash("You have logged out.", "info")
    return redirect(url_for('home'))  # go back to home page (index.html)

@app.route('/profile')
@login_required
def profile():
    user = current_user  # Flask-Login gives access to logged-in user
    return render_template('profile.html', user=user)

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

@app.route('/admin/home')
@login_required
def admin_home():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    # --- Counts ---
    lost_count = LostPet.query.filter_by(status='approved').count()
    found_count = FoundPet.query.filter_by(status='approved').count()
    adopt_count = AdoptPet.query.filter_by(status='pending').count()
    total_pets = lost_count + found_count + adopt_count

    total_users = User.query.filter_by(role='user').count()  # only normal users
    pending_requests = AdoptRequest.query.filter_by(status='pending').count()

    return render_template(
        'admin_index.html',
        user=current_user,
        lost_count=lost_count,
        found_count=found_count,
        adopt_count=adopt_count,
        total_pets=total_pets,
        total_users=total_users,
        pending_requests=pending_requests
    )

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

    chat_rooms = ChatRoom.query.filter_by(pet_id=pet.id).all()
    for room in chat_rooms:
        ChatMessage.query.filter_by(room_id=room.id).delete()

    ChatRoom.query.filter_by(pet_id=pet.id).delete()

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

    # Fetch all pets (we’ll separate them in the template)
    pets = AdoptPet.query.order_by(AdoptPet.id.desc()).all()

    pet_data = []
    pending_count = 0
    adopted_count = 0

    for pet in pets:
        requests = db.session.query(
            AdoptRequest,
            User.name.label('user_name'),
            User.email.label('user_email')
        ).join(User, AdoptRequest.user_id == User.id) \
         .filter(AdoptRequest.pet_id == pet.id) \
         .order_by(AdoptRequest.id.desc()) \
         .all()

        pet_data.append({
            'pet': pet,
            'requests': requests
        })

        if pet.status == 'pending':
            pending_count += 1 
        elif pet.status == 'adopted':
            adopted_count += 1

    return render_template(
        'admin_adopt.html',
        pet_data=pet_data,
        pending_count=pending_count,
        adopted_count=adopted_count,
        user=current_user
    )


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
            status="pending",
            pet_status="lost"
        )
        db.session.add(new_pet)
        db.session.commit()

        flash('Lost pet reported successfully!')
        return redirect(url_for('report_lost'))
    
    lost_pets = LostPet.query.filter_by(status='approved').order_by(LostPet.id.desc()).all()
    chat_room = ChatRoom.query.filter(
        ((ChatRoom.user1_id == current_user.id) | (ChatRoom.user2_id == current_user.id)) &
        (ChatRoom.active == True)
    ).first()
    return render_template('report_lost.html', user=current_user, lost_pets=lost_pets, chat_room=chat_room)

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
            status="pending",
            pet_status="found"
        )
        db.session.add(new_pet)
        db.session.commit()

        flash('Found pet reported successfully!')
        return redirect(url_for('report_found'))
    
    found_pets = FoundPet.query.filter_by(status='approved').order_by(FoundPet.id.desc()).all()
    chat_room = FoundChatRoom.query.filter(
        ((FoundChatRoom.user1_id == current_user.id) | (FoundChatRoom.user2_id == current_user.id)) &
        (FoundChatRoom.active == True)
    ).first()
    return render_template('report_found.html', user=current_user, found_pets=found_pets, chat_room=chat_room)

@app.route('/user/my_found_requests')
@login_required
def my_found_requests():
    user_id = current_user.id
    pets = FoundPet.query.filter_by(user_id=user_id).all()
    return render_template('my_found_request.html',user=current_user, pets=pets)

@app.route('/submit_found_request/<int:pet_id>', methods=['POST'])
@login_required
def submit_found_request(pet_id):
    name = request.form.get('name')
    address = request.form.get('address')
    mobile = request.form.get('mobile')
    description = request.form.get('description')
    image_file = request.files.get('image')

    if image_file and image_file.filename != "":
        safe_filename = secure_filename(image_file.filename)
        image_path = os.path.join('static/images', safe_filename)
        image_file.save(image_path)
    else:
        safe_filename = None

    found_request = FoundRequest(
        pet_id=pet_id,
        finder_id=current_user.id,
        name=name,
        address=address,
        mobile=mobile,
        description=description,
        image=safe_filename,
        status="pending",
        date_reported=datetime.utcnow()
    )

    db.session.add(found_request)
    db.session.commit()

    flash("Your found pet request has been submitted successfully!", "success")
    return redirect(url_for('report_lost'))

@app.route('/submit_claim_request/<int:pet_id>', methods=['POST'])
@login_required
def submit_claim_request(pet_id):
    name = request.form.get('name')
    address = request.form.get('address')
    mobile = request.form.get('mobile')
    description = request.form.get('description')
    image_file = request.files.get('image')

    # Handle file upload
    if image_file and image_file.filename != "":
        safe_filename = secure_filename(image_file.filename)
        image_path = os.path.join('static/images', safe_filename)
        image_file.save(image_path)
    else:
        safe_filename = None

    # Create new claim request
    claim_request = ClaimRequest(
        pet_id=pet_id,
        owner_id=current_user.id,
        name=name,
        address=address,
        mobile=mobile,
        description=description,
        image=safe_filename,
        status="pending",
        date_reported=datetime.utcnow()
    )

    db.session.add(claim_request)
    db.session.commit()

    flash("Your claim request has been submitted successfully!", "success")
    return redirect(url_for('report_found'))

@app.route('/found_pets')
@login_required
def found_pets():
    pets = FoundPet.query.filter_by(status='approved').all()
    return render_template('found_pet.html', user=current_user, pets=pets)

@app.route('/admin/lost_found')
@login_required
def admin_lost_found():
    found_requests = FoundRequest.query.order_by(FoundRequest.id.desc()).all()
    claim_requests = ClaimRequest.query.order_by(ClaimRequest.id.desc()).all()

    for req in found_requests:
        req.chat_room = ChatRoom.query.filter_by(found_request_id=req.id).first()

    for claim in claim_requests:
        claim.chat_room = FoundChatRoom.query.filter_by(claim_request_id=claim.id).first()

    return render_template('admin_lost_found.html', found_requests=found_requests, claim_requests=claim_requests, ChatRoom=ChatRoom, FoundChatRoom=FoundChatRoom)


@app.route('/admin/approve_found_request/<int:request_id>', methods=['POST'])
def approve_found_request(request_id):
    req = FoundRequest.query.get_or_404(request_id)
    req.status = 'Approved'

    pet = LostPet.query.filter_by(id=req.pet_id).first()
    if pet:
        pet.pet_status = 'Founded'
        pet.founded_at = datetime.utcnow()   # Update pet status to 'founded'

        message = f"Thanks for reuniting '{pet.pet_name}' to its owner!"
        notif = Notification(user_id=pet.user_id, message=message)
        db.session.add(notif)

        chat_rooms = ChatRoom.query.filter_by(pet_id=pet.id).all()
        for room in chat_rooms:
            ChatMessage.query.filter_by(room_id=room.id).delete()
            db.session.delete(room)

    db.session.commit()
    flash('Found request approved!', 'success')
    return redirect(url_for('admin_lost_found'))

@app.route('/admin/reject_found_request/<int:request_id>', methods=['POST'])
def reject_found_request(request_id):
    req = FoundRequest.query.get_or_404(request_id)
    req.status = 'Rejected'

    pet = LostPet.query.filter_by(id=req.pet_id).first()
    if pet:
        chat_rooms = ChatRoom.query.filter_by(pet_id=pet.id).all()
        for room in chat_rooms:
            ChatMessage.query.filter_by(room_id=room.id).delete()
            db.session.delete(room)
    db.session.commit()
    flash('Found request rejected.', 'info')
    return redirect(url_for('admin_lost_found'))

@app.route('/admin/delete_found_request/<int:request_id>', methods=['POST'])
def delete_found_request(request_id):
    req = FoundRequest.query.get_or_404(request_id)
    db.session.delete(req)
    db.session.commit()
    flash('Found request deleted.', 'danger')
    return redirect(url_for('admin_lost_found'))

@app.route('/admin/approve_claim_request/<int:request_id>', methods=['POST'])
def approve_claim_request(request_id):
    req = ClaimRequest.query.get_or_404(request_id)
    req.status = 'Approved'

    pet = FoundPet.query.filter_by(id=req.pet_id).first()
    if pet:
        pet.pet_status = 'Claimed'
        pet.founded_at = datetime.utcnow()

    db.session.commit()
    flash('Claim request approved!', 'success')
    return redirect(url_for('admin_lost_found'))


@app.route('/admin/reject_claim_request/<int:request_id>', methods=['POST'])
def reject_claim_request(request_id):
    req = ClaimRequest.query.get_or_404(request_id)
    req.status = 'Rejected'
    db.session.commit()
    flash('Claim request rejected.', 'info')
    return redirect(url_for('admin_lost_found'))


@app.route('/admin/delete_claim_request/<int:request_id>', methods=['POST'])
def delete_claim_request(request_id):
    req = ClaimRequest.query.get_or_404(request_id)
    db.session.delete(req)
    db.session.commit()
    flash('Claim request deleted.', 'danger')
    return redirect(url_for('admin_lost_found'))

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

@app.route("/admin/adopt_requests")
@login_required
def admin_adopt_requests():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('user_dashboard'))

    pets = AdoptPet.query.order_by(AdoptPet.id.desc()).all()
    pet_data = []

    for pet in pets:
        # Join adopt requests and user info
        requests = db.session.query(
            AdoptRequest,
            User.name.label('user_name'),
            User.email.label('user_email')
        ).join(User, AdoptRequest.user_id == User.id) \
         .filter(AdoptRequest.pet_id == pet.id) \
         .order_by(AdoptRequest.id.desc()).all()

        pet_data.append({
            "id": pet.id,
            "name": pet.pet_name,
            "type": pet.pet_type,
            "breed": pet.breed,           # added
            "location": pet.location,   # added
            "gender": pet.gender,     # added
            "description": pet.description,   # added
            "image": pet.image,      # added (if you store image filename)
            "requests": requests
        })

    return render_template("admin_adopt_requests.html", pets=pet_data)


@app.route('/admin/update_adopt_request/<int:req_id>/<string:action>', methods=['POST'])
@login_required
def update_adopt_request(req_id, action):
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    req = AdoptRequest.query.get_or_404(req_id)
    pet = AdoptPet.query.get(req.pet_id)
    user = User.query.get(req.user_id)

    if action == "approve":
        req.status = "approved"
        pet.status = "adopted"  # ✅ update pet to adopted
        message = f"Your adoption request for '{pet.pet_name}' has been approved!"
        subject = "Adoption Request Approved - PetConnect"
        flash(f"Adoption request for {pet.pet_name} approved!", "success")

    elif action == "reject":
        req.status = "rejected"
        message = f"Your adoption request for '{pet.pet_name}' has been rejected."
        subject = "Adoption Request Approved - PetConnect"
        flash(f"Adoption request for {pet.pet_name} rejected!", "warning")
    else:
        flash("Invalid action.", "danger")
        return redirect(url_for('admin_adopt_requests'))

    # Create notification for the requester
    notif = Notification(user_id=req.user_id, message=message)
    db.session.add(notif)

    db.session.delete(req)  # Remove request after decision
    db.session.commit()

    try:
        # Send email notification
        msg = Message(subject, recipients=[user.email])
        msg.body = f"Hello {user.name},\n\n{message}\n\nThankyou for using PetConnect!"
        msg.html = render_template('email_template.html', user=user, pet=pet, message=message, now=datetime.utcnow)
        mail.send(msg)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

    return redirect(url_for('admin_adopt_requests'))

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

@app.route('/update_found_edit', methods=['POST'])
@login_required
def update_found_edit():
    pet_id = request.form.get('pet_id')
    pet = FoundPet.query.filter_by(id=pet_id, user_id=current_user.id).first()

    if not pet:
        flash("Pet not found or you are not authorized.", "danger")
        return redirect(url_for('my_found_request'))

    # Update fields
    pet.pet_name = request.form.get('pet_name')
    pet.pet_type = request.form.get('pet_type')
    pet.breed = request.form.get('breed')
    pet.description = request.form.get('description')
    pet.gender = request.form.get('gender')
    pet.date_found = request.form.get('date_found')
    pet.found_location = request.form.get('found_location')
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
    return redirect(url_for('my_found_requests'))

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name')
    mobile = request.form.get('mobile')
    address = request.form.get('address')

    current_user.name = name
    current_user.mobile = mobile
    current_user.address = address
    db.session.commit()

    flash("Profile updated successfully!", "success")
    return redirect(url_for('profile'))

# ----------- Chat System For Lost Pet-----------

@app.route('/admin/enable_chat/<int:found_request_id>', methods=['POST'])
@login_required
def enable_chat(found_request_id):
    if current_user.role != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for('admin_lost_found'))

    found_req = FoundRequest.query.get_or_404(found_request_id)
    pet = LostPet.query.get(found_req.pet_id)

    # ✅ Allow enabling only if pet_status = 'Lost'
    if pet.pet_status != 'lost':
        flash("Chat can only be enabled for lost pets.", "warning")
        return redirect(url_for('admin_lost_found'))

    # ✅ Create or activate chat room
    chat_room = ChatRoom.query.filter_by(found_request_id=found_request_id).first()

    if not chat_room:
        chat_room = ChatRoom(
            pet_id=pet.id,
            user1_id=pet.user_id,  # Pet owner
            user2_id=found_req.finder_id,  # Finder
            found_request_id=found_request_id,
            active=True
        )
        db.session.add(chat_room)
    else:
        chat_room.active = True  # Reactivate if previously disabled

    db.session.commit()
    flash("Chat system activated successfully!", "success")
    return redirect(url_for('admin_lost_found'))

@app.route('/admin/disable_chat/<int:found_request_id>', methods=['POST'])
@login_required
def disable_chat(found_request_id):
    if not current_user.role == "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for('admin_lost_found'))

    chat_room = ChatRoom.query.filter_by(found_request_id=found_request_id).first()
    if chat_room:
        chat_room.active = False
        db.session.commit()
        flash("Chat system disabled.", "info")
    else:
        flash("No active chat found.", "warning")

    return redirect(url_for('admin_lost_found'))

@app.route('/chat/<int:room_id>')
@login_required
def get_chat_messages(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    if not room.active:
        return jsonify({'error': 'Chat is not active'}), 403

    messages = (
        db.session.query(ChatMessage, User)
        .join(User, ChatMessage.sender_id == User.id)
        .filter(ChatMessage.room_id == room_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )

    data = [
        {
            'sender_id': msg.ChatMessage.sender_id,
            'sender_name': msg.User.name,  # ✅ Add sender name here
            'message': msg.ChatMessage.message,
            'timestamp': msg.ChatMessage.timestamp.strftime('%Y-%m-%d %H:%M')
        }
        for msg in messages
    ]

    return jsonify(data)


@app.route('/chat/send/<int:room_id>', methods=['POST'])
@login_required
def send_message(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    if not room.active:
        return jsonify({'error': 'Chat not active'}), 403

    message = request.json.get('message')
    if not message.strip():
        return jsonify({'error': 'Empty message'}), 400

    msg = ChatMessage(room_id=room.id, sender_id=current_user.id, message=message)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/chat_rooms')
@login_required
def admin_chat_rooms():
    if current_user.role != "admin":
        flash('Access denied.')
        return redirect(url_for('user_dashboard'))

    room_data = []

    # 🟠 LOST PET CHAT ROOMS
    lost_chat_rooms = ChatRoom.query.filter_by(active=True).all()
    for room in lost_chat_rooms:
        lost_pet = LostPet.query.get(room.pet_id)
        if not lost_pet:
            continue

        user1 = User.query.get(room.user1_id)
        user2 = User.query.get(room.user2_id)

        pet_data = {
            'id': lost_pet.id,
            'pet_name': lost_pet.pet_name,
            'pet_type': lost_pet.pet_type,
            'breed': lost_pet.breed,
            'gender': lost_pet.gender,
            'description': lost_pet.description,
            'last_seen_location': lost_pet.last_seen_location,
            'image': lost_pet.image,
            'pet_status': lost_pet.pet_status
        }

        room_data.append({
            'room': room,
            'pet': pet_data,
            'user1': user1,
            'user2': user2,
            'category': 'LostPet'   # 👈 Add category label
        })

    # 🟢 FOUND PET CHAT ROOMS
    found_chat_rooms = FoundChatRoom.query.filter_by(active=True).all()
    for room in found_chat_rooms:
        found_pet = FoundPet.query.get(room.pet_id)
        if not found_pet:
            continue

        user1 = User.query.get(room.user1_id)
        user2 = User.query.get(room.user2_id)

        pet_data = {
            'id': found_pet.id,
            'pet_name': found_pet.pet_name,
            'pet_type': found_pet.pet_type,
            'breed': found_pet.breed,
            'gender': found_pet.gender,
            'description': found_pet.description,
            'found_location': found_pet.found_location,
            'image': found_pet.image,
            'pet_status': found_pet.pet_status
        }

        room_data.append({
            'room': room,
            'pet': pet_data,
            'user1': user1,
            'user2': user2,
            'category': 'FoundPet'   # 👈 Add category label
        })

    return render_template('admin_chat_rooms.html', rooms=room_data)

# -----------Chat System For Found Pet-----------

@app.route('/admin/enable_chat_claim/<int:claim_request_id>', methods=['POST'])
@login_required
def enable_chat_claim(claim_request_id):
    if current_user.role != "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for('admin_lost_found'))

    claim_req = ClaimRequest.query.get_or_404(claim_request_id)
    pet = FoundPet.query.get(claim_req.pet_id)

    # ✅ Allow enabling only if pet_status = 'Found'
    if pet.pet_status != 'found':
        flash("Chat can only be enabled for found pets.", "warning")
        return redirect(url_for('admin_lost_found'))

    # ✅ Create or activate chat room
    chat_room = FoundChatRoom.query.filter_by(claim_request_id=claim_request_id).first()

    if not chat_room:
        chat_room = FoundChatRoom(
            pet_id=pet.id,
            user1_id=pet.user_id,  # Pet finder
            user2_id=claim_req.owner_id,  # Pet owner
            claim_request_id=claim_request_id,
            active=True
        )
        db.session.add(chat_room)
    else:
        chat_room.active = True  # Reactivate if previously disabled

    db.session.commit()
    flash("Chat system activated successfully for claim request!", "success")
    return redirect(url_for('admin_lost_found'))

@app.route('/admin/disable_chat_claim/<int:claim_request_id>', methods=['POST'])
@login_required
def disable_chat_claim(claim_request_id):
    if not current_user.role == "admin":
        flash("Unauthorized access", "danger")
        return redirect(url_for('admin_lost_found'))

    chat_room = FoundChatRoom.query.filter_by(claim_request_id=claim_request_id).first()
    if chat_room:
        chat_room.active = False
        db.session.commit()
        flash("Chat system disabled.", "info")
    else:
        flash("No active chat found.", "warning")

    return redirect(url_for('admin_lost_found'))

@app.route('/found_chat/send/<int:room_id>', methods=['POST'])
@login_required
def send_found_message(room_id):
    room = FoundChatRoom.query.get_or_404(room_id)
    if not room.active:
        return jsonify({'error': 'Chat not active'}), 403

    message = request.json.get('message')
    if not message.strip():
        return jsonify({'error': 'Empty message'}), 400

    msg = FoundChatMessage(room_id=room.id, sender_id=current_user.id, message=message)
    db.session.add(msg)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/found_chat/<int:room_id>')
@login_required
def get_found_chat_messages(room_id):
    room = FoundChatRoom.query.get_or_404(room_id)
    if not room.active:
        return jsonify({'error': 'Chat is not active'}), 403

    messages = (
        db.session.query(FoundChatMessage, User)
        .join(User, FoundChatMessage.sender_id == User.id)
        .filter(FoundChatMessage.room_id == room_id)
        .order_by(FoundChatMessage.timestamp.asc())
        .all()
    )

    data = [
        {
            'sender_id': msg.FoundChatMessage.sender_id,
            'sender_name': msg.User.name,  # ✅ Add sender name here
            'message': msg.FoundChatMessage.message,
            'timestamp': msg.FoundChatMessage.timestamp.strftime('%Y-%m-%d %H:%M')
        }
        for msg in messages
    ]

    return jsonify(data)

# ----------- Admin User Creation -----------
with app.app_context():
    admins = [
        {
            "name": "Administrator-1",
            "email": "admin1@petrescue.com",
            "password": "admin123",
            "mobile": "N/A",
            "address": "Head Office"
        },
        {
            "name": "Administrator-2",
            "email": "admin2@petrescue.com",
            "password": "admin1234",
            "mobile": "N/A",
            "address": "Main Branch"
        }
    ]

    for admin in admins:
        admin_user = User.query.filter_by(email=admin["email"]).first()
        if not admin_user:
            hashed_password = bcrypt.generate_password_hash(admin["password"]).decode('utf-8')
            new_admin = User(
                name=admin["name"],
                mobile=admin["mobile"],
                email=admin["email"],
                address=admin["address"],
                password=hashed_password,
                role="admin"
            )
            db.session.add(new_admin)
            db.session.commit()
            print(f"✅ Admin user created: {admin['email']} / {admin['password']}")
        else:
            print(f"ℹ️ Admin already exists: {admin['email']}")

def move_found_pets_to_adopt():
    while True:
        with app.app_context():
            now = datetime.utcnow()
            threshold = now - timedelta(days=7)

            old_pets = FoundPet.query.filter(
                FoundPet.date_reported < threshold,
                FoundPet.status == 'approved',
                FoundPet.pet_status == 'found'
            ).all()

            for pet in old_pets:
                    # 1️⃣ Create AdoptPet entry
                    adopt_pet = AdoptPet(
                        pet_id = pet.id,
                        user_id=pet.user_id,
                        pet_name=pet.pet_name or "Unknown",
                        pet_type=pet.pet_type,
                        breed=pet.breed,
                        description=pet.description,
                        age="Unknown",
                        injury="No",
                        mobile=pet.mobile,
                        gender=pet.gender,
                        location=pet.found_location,
                        image=pet.image,
                        status="pending"
                    )
                    db.session.add(adopt_pet)
                    db.session.flush()  # ensures adopt_pet.id is available

                    # 2️⃣ Update ClaimRequests that referenced old FoundPet
                    related_claims = ClaimRequest.query.filter_by(pet_id=pet.id).all()
                    for claim in related_claims:
                        db.session.delete(claim)

                    # 3️⃣ Now it's safe to delete the old FoundPet
                    db.session.delete(pet)
                    db.session.commit()

            if old_pets:
                db.session.commit()

        time.sleep(60)


# Start background thread
thread = threading.Thread(target=move_found_pets_to_adopt, daemon=True)
thread.start()

# ----------- Scheduled Task: Remove Founded Pets After 24 Hours -----------
def remove_founded_pets():
    with app.app_context():
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        old_founded_pets = LostPet.query.filter(LostPet.pet_status=='Founded', LostPet.founded_at <= one_day_ago).all()

        for pet in old_founded_pets:
            db.session.delete(pet)
        db.session.commit()

        if old_founded_pets:
            print(f"✅ Removed {len(old_founded_pets)} founded pets from records.")

schedular.add_job(id='RemoveFoundedPets', func=remove_founded_pets, trigger='interval', hours=1)
schedular.start()
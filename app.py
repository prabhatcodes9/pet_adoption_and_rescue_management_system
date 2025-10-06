from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
from flask import jsonify

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
    date_found = db.Column(db.Date)
    mobile = db.Column(db.String(15))
    gender = db.Column(db.String(10))
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")

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
    return render_template('dashboard.html', user=current_user)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))
    
    lost_count = LostPet.query.count()
    found_count = FoundPet.query.count()  # Placeholder for FoundPet model
    adopt_count = 0  # Placeholder for AdoptPet model

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

@app.route('/admin/lost_pets')
@login_required
def admin_lost_pets():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    pets = LostPet.query.order_by(LostPet.id.desc()).all()
    return render_template('admin_lost.html', pets=pets, user=current_user)

@app.route('/admin/found_pets')
@login_required
def admin_found_pets():
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    pets = FoundPet.query.order_by(FoundPet.id.desc()).all()
    return render_template('admin_found.html', pets=pets, user=current_user)

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
    elif action == 'reject':
        pet.status = 'rejected'
        flash(f"{pet.pet_name} report rejected.", "warning")
    
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
    elif action == 'reject':
        pet.status = 'rejected'
        flash(f"{pet.pet_name} found report rejected.", "warning")
    else:
        flash("Invalid action.", "danger")
        return redirect(url_for('admin_found_pets'))

    db.session.commit()
    return redirect(url_for('admin_found_pets'))


@app.route('/admin/edit_pet/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def edit_pet(pet_id):
    if current_user.role != "admin":
        flash("Access denied!", "danger")
        return redirect(url_for('login'))

    pet = LostPet.query.get_or_404(pet_id)

    if request.method == 'POST':
        pet.pet_name = request.form.get('pet_name')
        pet.pet_type = request.form.get('pet_type')
        pet.breed = request.form.get('breed')
        pet.description = request.form.get('description')
        pet.last_seen_location = request.form.get('last_seen_location')
        pet.mobile = request.form.get('mobile')
        pet.gender = request.form.get('gender')
        pet.date_lost = request.form.get('date_lost')

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = image_file.filename
            image_file.save(os.path.join('static/uploads', filename))
            pet.image = filename

        db.session.commit()
        flash("Pet updated successfully!", "success")
        return redirect(url_for('admin_lost_pets'))

    return render_template('edit_pet.html', pet=pet, user=current_user)


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
        return redirect(url_for('user_dashboard'))
    
    lost_pets = LostPet.query.filter_by(status='approved').order_by(LostPet.id.desc()).all()
    return render_template('report_lost.html', user=current_user, lost_pets=lost_pets)

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
        return redirect(url_for('user_dashboard'))
    
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
    # later you’ll create AdoptPet model, same style
    return render_template('adopt_pet.html', user=current_user)

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
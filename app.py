from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os

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
    return render_template('admin_dashboard.html', user=current_user)

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
            image=filename
        )
        db.session.add(new_pet)
        db.session.commit()

        flash('Lost pet reported successfully!')
        return redirect(url_for('dashboard'))
    
    return render_template('report_lost.html', user=current_user)

@app.route('/user/my_lost_requests')
@login_required
def my_lost_requests():
    pets = LostPet.query.filter_by(user_id=current_user.id).all()
    return render_template('my_lost_requests.html',user=current_user, pets=pets)

@app.route('/lost_pets')
@login_required
def lost_pets():
    pets = LostPet.query.all()  # fetch all lost pets, not just current user
    return render_template('lost_pet.html', pets=pets, user=current_user)

@app.route('/found_pets')
@login_required
def found_pets():
    # later you’ll create FoundPet model, same style
    return render_template('found_pet.html', user=current_user)

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
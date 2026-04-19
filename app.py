from flask import (Flask, request, render_template, send_file,
                   redirect, url_for, flash, jsonify)
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user,
                         logout_user, login_required, current_user)
from flask_mail import Mail, Message
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from fpdf import FPDF
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import io, joblib, numpy as np, os, pandas as pd, plotly, plotly.express as px
import plotly.graph_objects as go, json, random
from datetime import datetime, timedelta
from dotenv import load_dotenv

from flask import send_file, redirect, url_for, flash
from flask_login import login_required, current_user
from fpdf import FPDF
from datetime import datetime
import io

# Load environment variables from .env file
load_dotenv()
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

# ═══════════════════════════════ APP SETUP ═══════════════════════════════════
app = Flask(__name__)
app.config['SECRET_KEY'] = 'loan-secret-2026'

# Session & Security configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════ DATABASE ════════════════════════════════════
DB_PATH = os.path.join(BASE_DIR, 'database', 'loans.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ═══════════════════════════════ FLASK-LOGIN ═════════════════════════════════
login_manager = LoginManager(app)
login_manager.login_view = 'register'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# ═══════════════════════════════ MAIL CONFIG ═════════════════════════════════
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'localhost')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 25))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

# ═══════════════════════════════ SOCKETIO ════════════════════════════════════
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ═══════════════════════════════ FILE UPLOAD ═════════════════════════════════
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'database')
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ═══════════════════════════════ DB MODELS ═══════════════════════════════════

class User(UserMixin, db.Model):
    """Registered user account."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('LoanApplication', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    otp = db.Column(db.String(6))
    otp_expiry = db.Column(db.DateTime)


class LoanApplication(db.Model):
    """Prediction record stored per user session."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email = db.Column(db.String(120))
    gender = db.Column(db.String(10))
    married = db.Column(db.String(10))
    dependents = db.Column(db.String(10))
    education = db.Column(db.String(20))
    employed = db.Column(db.String(10))
    credit = db.Column(db.Float)
    area = db.Column(db.String(20))
    applicant_income = db.Column(db.Float)
    coapplicant_income = db.Column(db.Float)
    loan_amount = db.Column(db.Float)
    loan_amount_term = db.Column(db.Float)
    prediction = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    credit_score = db.Column(db.Integer)
    reason = db.Column(db.String(512))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()

# ═══════════════════════════════ LOAD MODEL ══════════════════════════════════
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'Prediction Model')
# Fallback to root if models/ copy doesn't exist yet
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.join(BASE_DIR, 'Prediction Model')
model = joblib.load(MODEL_PATH)


# ═══════════════════════════════ HELPER FUNCTIONS ════════════════════════════

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def encode_features(form):
    """Parse and one-hot-encode form inputs; returns feature list or raises ValueError."""
    try:
        gender = form['gender']
        married = form['married']
        dependents = form['dependents']
        education = form['education']
        employed = form['employed']
        credit = float(form['credit'])
        area = form['area']
        ApplicantIncome = float(form['ApplicantIncome'])
        CoapplicantIncome = float(form['CoapplicantIncome'])
        LoanAmount = float(form['LoanAmount'])
        Loan_Amount_Term = float(form['Loan_Amount_Term'])
    except (KeyError, ValueError) as e:
        raise ValueError(f"Missing or invalid field: {e}")

    # ── Validation ──────────────────────────────────────────────────────────
    if ApplicantIncome < 0:
        raise ValueError("Applicant income cannot be negative.")
    if CoapplicantIncome < 0:
        raise ValueError("Co-applicant income cannot be negative.")
    if LoanAmount <= 0:
        raise ValueError("Loan amount must be greater than zero.")
    if Loan_Amount_Term <= 0:
        raise ValueError("Loan term must be greater than zero.")

    # ── Encoding ────────────────────────────────────────────────────────────
    male = 1 if gender == "Male" else 0
    married_yes = 1 if married == "Yes" else 0
    dep1 = dep2 = dep3 = 0
    if dependents == '1':   dep1 = 1
    elif dependents == '2': dep2 = 1
    elif dependents == '3+': dep3 = 1
    not_graduate = 1 if education == "Not Graduate" else 0
    employed_yes = 1 if employed == "Yes" else 0
    semiurban = urban = 0
    if area == "Semiurban": semiurban = 1
    elif area == "Urban":   urban = 1

    # ── Log transforms ──────────────────────────────────────────────────────
    ai_log = np.log(ApplicantIncome + 1)
    total_log = np.log(ApplicantIncome + CoapplicantIncome + 1)
    la_log = np.log(LoanAmount + 1)
    lat_log = np.log(Loan_Amount_Term + 1)

    features = [credit, ai_log, la_log, lat_log, total_log,
                male, married_yes, dep1, dep2, dep3,
                not_graduate, employed_yes, semiurban, urban]

    raw = {
        'gender': gender, 'married': married, 'dependents': dependents,
        'education': education, 'employed': employed, 'credit': credit,
        'area': area, 'ApplicantIncome': ApplicantIncome,
        'CoapplicantIncome': CoapplicantIncome,
        'LoanAmount': LoanAmount, 'Loan_Amount_Term': Loan_Amount_Term
    }
    return features, raw


def generate_explanation(raw, prediction):
    """Return a human-readable multi-factor explanation for the prediction."""
    reasons = []
    credit = raw['credit']
    income = raw['ApplicantIncome']
    co_income = raw['CoapplicantIncome']
    loan_amt = raw['LoanAmount']
    total_income = income + co_income
    area = raw['area']
    education = raw['education']
    employed = raw['employed']

    # Credit history — strongest factor
    if credit == 0:
        reasons.append("❌ No credit history (highest risk factor)")
    else:
        reasons.append("✅ Good credit history (strongest approval factor)")

    # Income-to-Loan ratio
    loan_inr = loan_amt * 1000
    ratio = loan_inr / max(total_income, 1)
    if ratio > 30:
        reasons.append(f"❌ Loan-to-income ratio is very high ({ratio:.1f}x)")
    elif ratio > 12:
        reasons.append(f"⚠️ Loan-to-income ratio is moderate ({ratio:.1f}x)")
    else:
        reasons.append(f"✅ Loan-to-income ratio is healthy ({ratio:.1f}x)")

    # Total income
    if total_income < 3000:
        reasons.append("❌ Total household income is low")
    elif total_income < 6000:
        reasons.append("⚠️ Total household income is moderate")
    else:
        reasons.append("✅ Strong total household income")

    # Co-applicant support
    if co_income > 0:
        reasons.append("✅ Co-applicant income adds financial strength")

    # Area
    if area == "Semiurban":
        reasons.append("✅ Semiurban area (favourable risk profile)")
    elif area == "Urban":
        reasons.append("✅ Urban area (good asset liquidity)")
    else:
        reasons.append("⚠️ Rural area (slightly higher risk)")

    # Education
    if education == "Graduate":
        reasons.append("✅ Graduate education improves eligibility")

    # Employment
    if employed == "Yes":
        reasons.append("⚠️ Self-employed (income variability factor)")

    verdict = "Loan APPROVED" if prediction == "approved" else "Loan REJECTED"
    primary = "Key factors behind the decision:" if prediction != "approved" else "Factors that supported approval:"
    return f"{verdict}. {primary} " + " | ".join(reasons)


def calculate_credit_score(income, loan_amount, credit_history, term):
    """Generate a simple 0–900 credit score."""
    score = 300  # base

    # Credit history contributes up to 350 points
    if credit_history == 1:
        score += 350
    else:
        score -= 100

    # Income level (up to 150 points)
    if income >= 10000:
        score += 150
    elif income >= 5000:
        score += 100
    elif income >= 2000:
        score += 50

    # Loan-to-income ratio (up to 100 points)
    loan_inr = loan_amount * 1000
    ratio = loan_inr / max(income, 1)
    if ratio <= 5:
        score += 100
    elif ratio <= 12:
        score += 60
    elif ratio <= 20:
        score += 20

    # Loan term (standard 360 months = slight bonus)
    if term == 360:
        score += 50
    elif term >= 240:
        score += 30

    return max(0, min(900, score))


def preprocess_train_csv(filepath):
    """Load and preprocess train.csv for model comparison / retraining."""
    df = pd.read_csv(filepath)
    df.dropna(inplace=True)

    # Encode categoricals
    le = LabelEncoder()
    cat_cols = ['Gender', 'Married', 'Education', 'Self_Employed',
                'Property_Area', 'Dependents', 'Loan_Status']
    for col in cat_cols:
        if col in df.columns:
            df[col] = le.fit_transform(df[col].astype(str))

    # Log transforms
    df['ApplicantIncomeLog'] = np.log(df['ApplicantIncome'] + 1)
    df['TotalIncomeLog'] = np.log(df['ApplicantIncome'] + df['CoapplicantIncome'] + 1)
    df['LoanAmountLog'] = np.log(df['LoanAmount'] + 1)
    df['Loan_Amount_TermLog'] = np.log(df['Loan_Amount_Term'] + 1)

    feature_cols = ['Credit_History', 'ApplicantIncomeLog', 'LoanAmountLog',
                    'Loan_Amount_TermLog', 'TotalIncomeLog', 'Gender', 'Married',
                    'Dependents', 'Education', 'Self_Employed',
                    'Property_Area']

    # Only keep columns that exist
    feature_cols = [c for c in feature_cols if c in df.columns]

    X = df[feature_cols]
    y = df['Loan_Status']
    return X, y


# ═══════════════════════════════ AUTH ROUTES ═════════════════════════════════

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
        elif password != confirm:
            flash('Passwords do not match.', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Auto-login after registration
            login_user(user)
            flash('Account created! Welcome to LoanDecide.', 'success')
            return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        # Allow login by username OR email
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            if remember:
                session.permanent = True
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}! 👋', 'success')
            return redirect(next_page or url_for('home'))
        flash('Invalid username or password. If you don\'t have an account, please register here.', 'danger')
        return redirect(url_for('register'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


from flask import session

def send_otp_email(user):
    otp = str(random.randint(100000, 999999))
    user.otp = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    
    msg = Message(
        subject="LoanDecide",
        sender=("LoanDecide", "vasoyaprince15@gmail.com"),
        recipients=[user.email]
    )
    msg.body = f'Your OTP for resetting password is: {otp}\nValid for 10 minutes.'
    
    # For now, we will print it to the console for verification
    print("\n" + "="*40)
    print("PASSWORD RESET OTP SENT")
    print(f"TO: {user.email}")
    print(f"OTP: {otp}")
    print("="*40 + "\n")
    
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")


@app.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            send_otp_email(user)
            session['reset_email'] = email
            flash('A 6-digit OTP has been sent to your email.', 'info')
            return redirect(url_for('verify_otp'))
        flash('If an account with that email exists, an OTP has been sent.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')


@app.route("/verify_otp", methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if 'reset_email' not in session:
        flash('Please enter your email first.', 'warning')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        otp_input = request.form.get('otp', '').strip()
        user = User.query.filter_by(email=session['reset_email']).first()
        
        if user and user.otp == otp_input and user.otp_expiry > datetime.utcnow():
            session['otp_verified'] = True
            # Clear OTP from DB after verification
            user.otp = None
            user.otp_expiry = None
            db.session.commit()
            flash('OTP Verified! Please set your new password.', 'success')
            return redirect(url_for('reset_password'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')
            
    return render_template('verify_otp.html')


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if not session.get('otp_verified'):
        flash('Please verify your OTP first.', 'warning')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        else:
            user = User.query.filter_by(email=session['reset_email']).first()
            if user:
                user.set_password(password)
                db.session.commit()
                session.pop('reset_email', None)
                session.pop('otp_verified', None)
                flash('Your password has been updated! You are now able to log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('An error occurred. Please try again.', 'danger')
                return redirect(url_for('forgot_password'))
    return render_template('reset_password.html')


# ═══════════════════════════════ MAIN ROUTES ═════════════════════════════════

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        # ── Validate & encode ────────────────────────────────────────────────
        try:
            features, raw = encode_features(request.form)
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('prediction.html')

        # ── Prediction + Confidence ──────────────────────────────────────────
        pred = model.predict([features])[0]
        try:
            proba = model.predict_proba([features])[0]
            confidence = round(float(max(proba)) * 100, 1)
        except Exception:
            confidence = None

        # ── Result & XAI ────────────────────────────────────────────────────
        if pred == "N":
            status = "rejected"
            verb = "Not Approved"
        else:
            status = "approved"
            verb = "Approved"

        conf_text = f"{verb} ({confidence}% confidence)" if confidence else verb
        explanation = generate_explanation(raw, status)
        credit_score = calculate_credit_score(
            raw['ApplicantIncome'], raw['LoanAmount'],
            raw['credit'], raw['Loan_Amount_Term']
        )

        # ── Save to DB ───────────────────────────────────────────────────────
        email_address = request.form.get('email', 'not_provided@test.com')
        new_app = LoanApplication(
            user_id=current_user.id,
            email=email_address,
            gender=raw['gender'], married=raw['married'],
            dependents=raw['dependents'], education=raw['education'],
            employed=raw['employed'], credit=raw['credit'],
            area=raw['area'],
            applicant_income=raw['ApplicantIncome'],
            coapplicant_income=raw['CoapplicantIncome'],
            loan_amount=raw['LoanAmount'],
            loan_amount_term=raw['Loan_Amount_Term'],
            prediction=status, confidence=confidence,
            credit_score=credit_score, reason=explanation
        )
        db.session.add(new_app)
        db.session.commit()

        # ── Real-time update ─────────────────────────────────────────────────
        socketio.emit('new_approval', {
            'text': f"Loan ₹{int(raw['LoanAmount'] * 1000):,} was {status}",
            'time': 'Just now'
        })
        print(f"\nEMAIL TO: {email_address} | Result: {conf_text} | Score: {credit_score}\n")

        return render_template(
            'prediction.html',
            prediction_text=conf_text,
            status=status,
            confidence=confidence,
            credit_score=credit_score,
            explanation=explanation,
            app_id=new_app.id
        )
    return render_template('prediction.html')


# ═══════════════════════════════ PREDICTION HISTORY ══════════════════════════

@app.route('/history')
@login_required
def history():
    apps = LoanApplication.query.filter_by(user_id=current_user.id)\
               .order_by(LoanApplication.timestamp.desc()).all()
    return render_template('history.html', apps=apps)


# ═══════════════════════════════ DASHBOARD ═══════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    apps = LoanApplication.query.all()
    if not apps:
        return render_template('dashboard.html', no_data=True)

    # ── Chart 1: Approval Rate Pie ───────────────────────────────────────────
    approved = sum(1 for a in apps if a.prediction == 'approved')
    rejected = len(apps) - approved
    fig1 = go.Figure(data=[go.Pie(
        labels=['Approved', 'Rejected'],
        values=[approved, rejected],
        hole=0.45,
        marker_colors=['#6366f1', '#f43f5e'],
        textinfo='label+percent',
        hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
    )])
    fig1.update_layout(
        title='Loan Approval Rate',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#e2e8f0',
        title_font_size=16,
        showlegend=True,
        legend=dict(font=dict(color='#e2e8f0'))
    )

    # ── Chart 2: Applicant Income vs Loan Amount Scatter ────────────────────
    incomes = [a.applicant_income for a in apps]
    loans = [a.loan_amount for a in apps]
    colors = ['#22c55e' if a.prediction == 'approved' else '#f43f5e' for a in apps]
    fig2 = go.Figure(data=[go.Scatter(
        x=incomes, y=loans,
        mode='markers',
        marker=dict(color=colors, size=9, opacity=0.75,
                    line=dict(width=1, color='rgba(255,255,255,0.2)')),
        text=[f"{'Approved' if a.prediction=='approved' else 'Rejected'}" for a in apps],
        hovertemplate='Income: ₹%{x}<br>Loan: ₹%{y}k<br>Status: %{text}<extra></extra>'
    )])
    fig2.update_layout(
        title='Applicant Income vs Loan Amount',
        xaxis_title='Applicant Income (₹)',
        yaxis_title='Loan Amount (₹ thousands)',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(13,13,26,0.8)',
        font_color='#e2e8f0',
        title_font_size=16,
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )

    # ── Chart 3: Property Area vs Loan Status Bar ────────────────────────────
    areas = ['Urban', 'Semiurban', 'Rural']
    area_approved = [sum(1 for a in apps if a.area == ar and a.prediction == 'approved') for ar in areas]
    area_rejected = [sum(1 for a in apps if a.area == ar and a.prediction == 'rejected') for ar in areas]
    fig3 = go.Figure(data=[
        go.Bar(name='Approved', x=areas, y=area_approved,
               marker_color='#6366f1', hovertemplate='%{x}: %{y} approved<extra></extra>'),
        go.Bar(name='Rejected', x=areas, y=area_rejected,
               marker_color='#f43f5e', hovertemplate='%{x}: %{y} rejected<extra></extra>')
    ])
    fig3.update_layout(
        barmode='group',
        title='Property Area vs Loan Status',
        xaxis_title='Property Area',
        yaxis_title='Number of Applications',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(13,13,26,0.8)',
        font_color='#e2e8f0',
        title_font_size=16,
        legend=dict(font=dict(color='#e2e8f0')),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
    )

    charts = {
        'pie': json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder),
        'scatter': json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder),
        'bar': json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder),
    }
    stats = {
        'total': len(apps),
        'approved': approved,
        'rejected': rejected,
        'rate': round(approved / len(apps) * 100, 1) if apps else 0
    }
    return render_template('dashboard.html', charts=charts, stats=stats, no_data=False)


# ═══════════════════════════════ ADMIN ═══════════════════════════════════════

@app.route('/admin')
@login_required
def admin():
    """Admin view to see all applications across all users."""
    apps = LoanApplication.query.order_by(LoanApplication.timestamp.desc()).all()
    return render_template('admin.html', apps=apps)


# ═══════════════════════════════ MODEL COMPARISON ════════════════════════════

@app.route('/model-comparison')
@login_required
def model_comparison():
    train_path = os.path.join(BASE_DIR, 'train.csv')
    if not os.path.exists(train_path):
        flash('train.csv not found in project root.', 'warning')
        return render_template('model_comparison.html', results=None)

    try:
        X, y = preprocess_train_csv(train_path)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42)

        models_to_compare = {
            'Logistic Regression': LogisticRegression(max_iter=500),
            'Random Forest': RandomForestClassifier(n_estimators=50, random_state=42),
            'Decision Tree': DecisionTreeClassifier(random_state=42),
        }
        results = []
        best_acc = 0
        best_name = ''
        for name, m in models_to_compare.items():
            m.fit(X_train, y_train)
            acc = round(accuracy_score(y_test, m.predict(X_test)) * 100, 2)
            results.append({'model': name, 'accuracy': acc})
            if acc > best_acc:
                best_acc = acc
                best_name = name

        # Plotly bar chart
        fig = go.Figure(data=[go.Bar(
            x=[r['model'] for r in results],
            y=[r['accuracy'] for r in results],
            marker_color=['#6366f1', '#a855f7', '#06b6d4'],
            text=[f"{r['accuracy']}%" for r in results],
            textposition='outside',
            hovertemplate='%{x}: %{y}%<extra></extra>'
        )])
        fig.update_layout(
            title='Model Accuracy Comparison',
            yaxis_title='Accuracy (%)',
            yaxis_range=[0, 110],
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(13,13,26,0.8)',
            font_color='#e2e8f0',
            title_font_size=16,
            xaxis=dict(gridcolor='rgba(0,0,0,0)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
        )
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('model_comparison.html',
                               results=results, best=best_name,
                               chart=chart_json)
    except Exception as e:
        flash(f'Error during model comparison: {str(e)}', 'danger')
        return render_template('model_comparison.html', results=None)


# ═══════════════════════════════ MODEL RETRAINING ════════════════════════════

@app.route('/retrain', methods=['GET', 'POST'])
@login_required
def retrain():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded.', 'danger')
            return redirect(request.url)
        f = request.files['file']
        if f.filename == '' or not allowed_file(f.filename):
            flash('Please upload a valid CSV file.', 'danger')
            return redirect(request.url)
        try:
            filename = secure_filename(f.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(filepath)

            X, y = preprocess_train_csv(filepath)
            new_model = RandomForestClassifier(n_estimators=100, random_state=42)
            new_model.fit(X, y)

            save_path = os.path.join(BASE_DIR, 'models', 'Prediction Model')
            joblib.dump(new_model, save_path)

            # Reload global model
            global model
            model = joblib.load(save_path)

            flash('✅ Model retrained and saved successfully!', 'success')
        except Exception as e:
            flash(f'❌ Retraining failed: {str(e)}', 'danger')
        return redirect(url_for('retrain'))
    return render_template('retrain.html')


# ═══════════════════════════════ DOWNLOAD REPORT ═════════════════════════════
      
@app.route('/download_report/<int:app_id>')
@login_required
def download_report(app_id):
    loan = LoanApplication.query.get_or_404(app_id)

    # सुरक्षा check
    if loan.user_id and loan.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('history'))

    # ✅ Safe text cleaner (handles encoding issues)
    def clean(text):
        if text is None:
            return ""
        return str(text).encode('latin-1', 'ignore').decode('latin-1')

    pdf = FPDF()
    pdf.add_page()

    # ===== Header =====
    pdf.set_fill_color(99, 102, 241)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", 'B', 18)
    pdf.cell(0, 14, clean("LoanDecide - Loan Application Report"), ln=True, align='C', fill=True)
    pdf.ln(6)

    # ===== Sub-header =====
    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(
        0, 8,
        clean(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | Application ID: #{loan.id}"),
        ln=True,
        align='C'
    )
    pdf.ln(8)

    # ===== Decision Status =====
    if loan.prediction == 'approved':
        pdf.set_fill_color(34, 197, 94)
        label = "APPROVED"
    else:
        pdf.set_fill_color(239, 68, 68)
        label = "REJECTED"

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 12, clean(f"Decision: {label}"), ln=True, align='C', fill=True)

    if loan.confidence:
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(0, 8, clean(f"Model Confidence: {loan.confidence}%"), ln=True, align='C')

    pdf.ln(10)

    # ===== Table =====
    pdf.set_text_color(20, 20, 20)
    col_w = [70, 120]

    def row(field, value, shade=False):
        if shade:
            pdf.set_fill_color(245, 245, 255)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(col_w[0], 9, clean(field), border=1, fill=True)

        pdf.set_font("Helvetica", '', 10)
        pdf.cell(col_w[1], 9, clean(value), border=1, fill=True, ln=True)

    rows_data = [
        ("Email", loan.email),
        ("Gender", loan.gender),
        ("Married", loan.married),
        ("Dependents", loan.dependents),
        ("Education", loan.education),
        ("Self Employed", loan.employed),
        ("Credit History", "Good" if loan.credit == 1 else "No History"),
        ("Property Area", loan.area),
        ("Applicant Income (Rs)", f"{loan.applicant_income or 0:,.0f}"),
        ("Co-applicant Income (Rs)", f"{loan.coapplicant_income or 0:,.0f}"),
        ("Loan Amount", f"{loan.loan_amount or 0:,.0f}k"),
        ("Loan Term", f"{loan.loan_amount_term or 0:.0f} months"),
        ("Credit Score", f"{loan.credit_score} / 900" if loan.credit_score else "N/A"),
    ]

    for i, (f, v) in enumerate(rows_data):
        row(f, v, shade=(i % 2 == 0))

    pdf.ln(8)

    # ===== AI Explanation =====
    if loan.reason:
        pdf.set_font("Helvetica", 'B', 11)
        pdf.cell(0, 9, clean("AI Decision Explanation:"), ln=True)

        pdf.set_font("Helvetica", '', 9)
        pdf.multi_cell(0, 7, clean(loan.reason))

    # ===== FIXED OUTPUT (no encode error) =====
    output = pdf.output(dest='S')

    # Handle both old/new FPDF versions safely
    if isinstance(output, str):
        pdf_bytes = output.encode('latin-1', 'ignore')
    else:
        pdf_bytes = bytes(output)

    return send_file(
        io.BytesIO(pdf_bytes),
        download_name=f"LoanDecide_Report_{loan.id}.pdf",
        as_attachment=True,
        mimetype='application/pdf'
    )

# ═══════════════════════════════ RUN ═════════════════════════════════════════

if __name__ == "__main__":
    socketio.run(
        app,
        host="127.0.0.1",
        port=5001,
        debug=True,
        use_reloader=False
    )

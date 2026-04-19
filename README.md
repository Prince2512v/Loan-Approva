# 🚀 LoanDecide: Loan Approval Prediction System

LoanDecide is a high-performance, full-stack machine learning web application designed to predict loan approval probabilities with high accuracy. It combines a sleek, modern "Glassmorphism" UI with robust back-end logic and Explainable AI (XAI) to provide users with transparent and actionable financial insights.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0+-000000?style=for-the-badge&logo=flask&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Latest-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Latest-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

---

## ✨ Key Features

### 🧠 Intelligent Prediction
- **ML Engine**: Uses a Random Forest Classifier to predict loan status based on 11+ financial parameters.
- **Explainable AI (XAI)**: Doesn't just give a "Yes/No". It provides a detailed breakdown of *why* a loan was approved or rejected (e.g., credit history impact, income-to-loan ratio).
- **Credit Scoring**: Generates a proprietary credit score (0–900) based on applicant data.

### 📊 Advanced Analytics
- **Live Dashboard**: Interactive Plotly charts showing approval rates, income vs. loan amount correlations, and property area trends.
- **Model Comparison**: Real-time accuracy benchmarking between Logistic Regression, Random Forest, and Decision Tree models.
- **Dynamic Retraining**: Administrators can upload new datasets (CSV) to retrain and update the production model instantly.

### 🔐 Secure & User-Centric
- **Authentication**: Secure JWT/Session-based login and registration.
- **OTP Password Reset**: Integrated email service for secure password recovery via 6-digit OTP.
- **PDF Reports**: Generate and download professional PDF reports for every loan application.
- **Real-time Updates**: Socket.IO integration for live notifications on global loan trends.

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, Vanilla CSS (Custom Glassmorphism Design System), JavaScript (ES6+).
- **Backend**: Flask (Python), SQLAlchemy ORM.
- **Machine Learning**: Scikit-learn, Pandas, NumPy, Joblib.
- **Visualizations**: Plotly.js / Plotly Python.
- **Security**: Werkzeug Security (Password Hashing), ItsDangerous (Tokenization).
- **Utilities**: Flask-Mail (OTP), FPDF (Report Generation), Flask-SocketIO (Real-time).

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python Package Installer)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Prince2512v/Loan-Approva.git
   cd Loan-Approva
   ```

2. **Set Up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # source venv/bin/activate    # On Linux/Mac
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory and add your mail settings (for OTP functionality):
   ```env
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

5. **Initialize Database & Run**
   ```bash
   python app.py
   ```
   The app will be available at `http://127.0.0.1:5000`.

---

## 📁 Project Structure

```text
├── app.py                  # Main Flask application logic
├── models/                 # Pre-trained ML models (Joblib)
├── static/                 # CSS, JavaScript, and Images
├── templates/              # HTML templates (Jinja2)
├── database/               # SQLite database file
├── train.csv / test.csv    # Datasets for training & testing
├── requirements.txt        # Project dependencies
└── .gitignore              # Files to exclude from Git
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
Developed with ❤️ by [Prince Vasoya](https://github.com/Prince2512v)

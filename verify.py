try:
    import flask, flask_sqlalchemy, flask_login, flask_socketio, flask_mail
    import fpdf, joblib, numpy, pandas, sklearn, plotly, werkzeug
    print("All imports OK")
    
    # Test model loading
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(BASE_DIR, 'models', 'Prediction Model')
    if not os.path.exists(model_path):
        model_path = os.path.join(BASE_DIR, 'Prediction Model')
    m = joblib.load(model_path)
    print(f"Model loaded: {type(m).__name__}")
    
    # Test predict_proba
    import numpy as np
    test_input = [[1, 8.5, 4.9, 5.9, 8.8, 1, 1, 0, 0, 0, 0, 0, 0, 1]]
    pred = m.predict(test_input)
    proba = m.predict_proba(test_input)
    print(f"Prediction: {pred[0]}, Confidence: {round(float(max(proba[0]))*100,1)}%")
    
    print("\nAll verifications PASSED!")
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()

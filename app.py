from flask import Flask, request, jsonify, render_template
import pickle
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler, LabelEncoder
from tensorflow.keras.preprocessing import image
import pandas as pd
import json
import os

app = Flask(__name__)

# Create upload folder for image predictions
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==================== Crop Recommendation Setup ====================
dataset = pd.read_csv('Crop_recommendation.csv')
X = dataset.iloc[:, :-1].values
y = dataset.iloc[:, -1].values

label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)

from sklearn.model_selection import train_test_split
X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2, random_state=0)

sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

with open('random_forest_model.pkl', 'rb') as model_file:
    crop_classifier = pickle.load(model_file)

# ==================== Disease Model Setup ====================
disease_model = tf.keras.models.load_model("model.h5")
with open("labels.json", "r") as f:
    disease_class_labels = json.load(f)

def preprocess_image(img_path):
    img = image.load_img(img_path, target_size=(128, 128))
    img_array = image.img_to_array(img) / 255.0
    return np.expand_dims(img_array, axis=0)

# ==================== Web Routes ====================
@app.route('/')
def login():
    return render_template('login.html', show_loader=True)

@app.route('/signup')
def signup():
    return render_template('signup.html', show_loader=True)

@app.route('/mainsec')
def mainsec():
    return render_template('mainpage.html', show_loader=True)

@app.route('/home')
def home():
    return render_template('home.html', show_loader=True)

@app.route('/team')
def team():
    return render_template('team.html', show_loader=True)

@app.route('/contact')
def contact():
    return render_template('contact.html', show_loader=True)

@app.route('/dis_pred')
def dis_pred():
    return render_template('dis_pred.html', show_loader=True)

# ==================== Crop Recommendation Endpoint ====================
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = [float(request.form[k]) for k in ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
        input_scaled = sc.transform([data])
        pred_encoded = crop_classifier.predict(input_scaled)
        label = label_encoder.inverse_transform(pred_encoded)
        return render_template('result.html', prediction=label[0])
    except Exception as e:
        return render_template('result.html', error=str(e))

# ==================== Disease Prediction Endpoint ====================
@app.route('/dis_predict', methods=['POST'])
def dis_predict():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error': 'No file uploaded'}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        img_array = preprocess_image(filepath)
        predictions = disease_model.predict(img_array)
        pred_index = str(np.argmax(predictions, axis=1)[0])
        label = disease_class_labels.get(pred_index, "Unknown")
        return jsonify({'prediction': label})
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

# ==================== Run App ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
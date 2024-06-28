import os

from flask import Flask, jsonify, request
from PIL import Image
import cv2
import numpy as np
import tensorflow as tf
import keras_ocr
import matplotlib.pyplot as plt
import pandas as pd
from werkzeug.utils import secure_filename

from src.firebase_module import postUsers, getUsers
from src.sayang_air_data import water_using, get_data_by_email

from src.firebase_module import postUsers

app = Flask(__name__)
app.config['MODEL_FILE'] = 'model_cnn_new.h5'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])

model = tf.keras.models.load_model(app.config['MODEL_FILE'], compile=False)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# @app.route('/predictnik', methods=["GET", "POST"])  
def predict_nik(image):
    # img = Image.open(image)
    # bounding box
    pipeline = keras_ocr.pipeline.Pipeline()
    images = [keras_ocr.tools.read(image)]
    results = pipeline.recognize(images)
    keras_ocr.tools.drawAnnotations(images[0], results[0])

    # titik koordinat yg membentuk bounding box pada NIK
    df = pd.DataFrame(results[0], columns=['text', 'bbox'])
    indices = len(df.index)
    index = 0

    for x in range(0, indices):
        if df.loc[x, 'text'] != 'nik':
            index += 1
        if df.loc[x, 'text'] == 'nik':
            break
    
    index_no_nik = index + 1
    bbox_coordinate = df.loc[index_no_nik, 'bbox']

    x1 = int(bbox_coordinate[0][0])
    y1 = int(bbox_coordinate[0][1])
    x2 = int(bbox_coordinate[2][0])
    y2 = int(bbox_coordinate[2][1])

    # crop bagian NIK sebesar bounding box
    img = cv2.imread(image)
    roi = img[y1: y2, x1: x2]

    # NIK image transformations
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # beri bounding box setiap angka pada NIK
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.boundingRect(x)[0])
    preprocessed_digits = []
    i = 0
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(roi, (x, y), (x+w, y+h), color=(255, 0, 0), thickness=1)
        digit = thresh[y:y+h, x:x+w]
        i += 1
        resized_digit = cv2.resize(digit, (18, 18))
        padded_digit = np.pad(resized_digit, ((5, 5), (5, 5)), 'constant', constant_values=0)
        preprocessed_digits.append(padded_digit)
    
    # prediksi

    digit_nik = []
    index = 0
    for digit in preprocessed_digits:
        prediction = model.predict(digit.reshape(1, 28, 28, 1))
        index +=1
        digit_nik.append(np.argmax(prediction))
    
    # hasil prediksi
    nik = ''
    for digit in digit_nik:
        nik += str(digit)
    return nik

@app.route("/")
def hello_world():
    resultTest = "Hello World!, ini adalah endpoint dari API sayang air"
    return resultTest


@app.route("/users", methods = ["GET"])
def get_users():
    return getUsers()

@app.route("/sayang-air", methods = ["GET"])
def get_water_using():
    return water_using

@app.route("/sayang-air/<email>", methods = ["GET"])
def get_water_using_by_email(email):
    return get_data_by_email(email)

@app.route("/prediction", methods=["POST"])
def predict_route():
    if request.method == "POST":
        image = request.files["image"]
        email_user = request.form.get('email')
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            nik = predict_nik(image_path)

            # if len(nik) < 10:
            #     return jsonify({
            #     "status": {
            #         "code": 400,
            #         "message": "KTP invalid!"
            #     },
            #     "data": {
            #         "nik": nik,
            #         "email": email_user
            #     }
            # }), 400

            result_post = postUsers(email_user, nik)

            if result_post:
                return jsonify({
                    "status": {
                        "code": 200,
                        "message": "Success predicting"
                    },
                    "data": {
                        "nik": nik,
                        "email": email_user
                    }
                }), 200
            else :
                return jsonify({
                    "status": {
                        "code": 500,
                        "message": "Something wrong"
                    },
                    "data": {
                        "msg": 'ok'
                    }
                }), 500
        else:
            return jsonify({
                "status": {
                    "code": 400,
                    "message": "Invalid file format. Please upload a JPG, JPEG, or PNG image."
                },
                "data": None,
            }), 400
    else:
        return jsonify({
            "status": {
                "code": 405,
                "message": "Method not allowed"
            },
            "data": None,
        }), 405

if __name__ == "__main__":
    app.run(debug=True)

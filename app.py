from flask import Flask, render_template, request, send_file
import os
import cv2
import numpy as np
import secrets

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        key = request.form.get('key')

        if not file or not key:
            return render_template('index.html', error="Lütfen bir resim ve anahtar girin!")

        key = int(key)
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        img = cv2.imread(filepath)
        h, w, c = img.shape

        # Rastgele permütasyon oluştur (her pikselin yerini karıştır)
        np.random.seed(key)
        perm = np.random.permutation(h * w)
        img_flat = img.reshape(-1, c)
        encrypted_flat = img_flat[perm]
        encrypted_img = encrypted_flat.reshape(h, w, c)

        enc_path = os.path.join(UPLOAD_FOLDER, 'encrypted_' + file.filename)
        cv2.imwrite(enc_path, encrypted_img)

        return render_template('index.html', original=file.filename, encrypted='encrypted_' + file.filename)

    return render_template('index.html')

@app.route('/decrypt', methods=['POST'])
def decrypt():
    file = request.files['image']
    key = request.form.get('key')

    if not file or not key:
        return render_template('index.html', error="Lütfen şifreli bir resim ve anahtar girin!")

    key = int(key)
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    img = cv2.imread(filepath)
    h, w, c = img.shape

    np.random.seed(key)
    perm = np.random.permutation(h * w)
    inv_perm = np.argsort(perm)

    img_flat = img.reshape(-1, c)
    decrypted_flat = img_flat[inv_perm]
    decrypted_img = decrypted_flat.reshape(h, w, c)

    dec_path = os.path.join(UPLOAD_FOLDER, 'decrypted_' + file.filename)
    cv2.imwrite(dec_path, decrypted_img)

    return render_template('index.html', decrypted='decrypted_' + file.filename)

if __name__ == '__main__':
    app.run(debug=True)

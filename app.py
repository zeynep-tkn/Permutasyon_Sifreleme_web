from flask import Flask, render_template, request, send_file
import os
import cv2
import numpy as np
import secrets

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def is_valid_permutation_key(key_str):
    """Anahtarın geçerli bir permütasyon olup olmadığını kontrol eder (örn: '35241')"""
    n = len(key_str)
    if n == 0 or n > 9:  # Ödev isterine göre en fazla 9
        return False, "Anahtar 1-9 basamaklı olmalıdır."
    
    try:
        # Anahtarın 1'den N'ye kadar olan sayıları tam olarak bir kez içermesi gerekir
        digits = [int(c) for c in key_str]
        expected_digits = set(range(1, n + 1))
        if set(digits) != expected_digits:
            return False, f"Anahtar, 1'den {n}'e kadar olan sayıları tam bir kez içermelidir (örn: 312)."
    except ValueError:
        return False, "Anahtar sadece sayılardan oluşmalıdır."
        
    return True, ""

def process_image(img, key_str, mode='encrypt'):
    """
    Görüntüyü anahtara göre bloklar halinde permüte eder.
    mode='encrypt' için şifreler, mode='decrypt' için deşifreler.
    """
    h, w, c = img.shape
    # Görüntüyü "düz metne" (piksel dizisine) çeviriyoruz
    img_flat = img.reshape(-1, c)
    total_pixels = h * w
    
    n = len(key_str)
    # Anahtarı 0-tabanlı indekslere çevir (örn: '35241' -> [2, 4, 1, 3, 0])
    perm_indices = [int(c) - 1 for c in key_str]
    
    if mode == 'decrypt':
        # Deşifreleme için permütasyonun tersini (argsort) kullanıyoruz
        # Bu, A->B ise B->A işlemini garanti eder
        perm_indices = list(np.argsort(perm_indices))

    # Çıktı için boş bir dizi oluştur
    processed_flat = np.zeros_like(img_flat)
    
    # Sadece N'ye tam bölünebilen kısmı şifrele/deşifrele
    # Bu, padding (dolgu) sorununu ve metadata saklama ihtiyacını ortadan kaldırır
    permutable_pixels = (total_pixels // n) * n
    
    for i in range(0, permutable_pixels, n):
        block = img_flat[i:i+n]
        
        # Permütasyonu uygula
        # (örn: encrypt_block[0] = block[perm_indices[0]] -> block[2])
        # (örn: decrypt_block[0] = block[inv_perm_indices[0]] -> block[4])
        for j in range(n):
            processed_flat[i + j] = block[perm_indices[j]]
            
    # Görüntünün geri kalan (artık) piksellerini (varsa) dokunmadan ekle
    if permutable_pixels < total_pixels:
        processed_flat[permutable_pixels:] = img_flat[permutable_pixels:]

    # "Düz metni" tekrar resim şekline dönüştür
    return processed_flat.reshape(h, w, c)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['image']
        key_str = request.form.get('key')

        if not file or not key_str:
            return render_template('index.html', error="Lütfen bir resim ve anahtar girin!")

        is_valid, error_msg = is_valid_permutation_key(key_str)
        if not is_valid:
            return render_template('index.html', error=error_msg)

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        img = cv2.imread(filepath)
        
        # Şifreleme işlemini yap
        encrypted_img = process_image(img, key_str, mode='encrypt')

        enc_path = os.path.join(UPLOAD_FOLDER, 'encrypted_' + file.filename)
        cv2.imwrite(enc_path, encrypted_img)

        return render_template('index.html', original=file.filename, encrypted='encrypted_' + file.filename)

    return render_template('index.html')

@app.route('/decrypt', methods=['POST'])
def decrypt():
    file = request.files['image']
    key_str = request.form.get('key')

    if not file or not key_str:
        return render_template('index.html', error="Lütfen şifreli bir resim ve anahtar girin!")
        
    is_valid, error_msg = is_valid_permutation_key(key_str)
    if not is_valid:
        return render_template('index.html', error=error_msg)

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    img = cv2.imread(filepath)
    
    # Deşifreleme işlemini yap
    decrypted_img = process_image(img, key_str, mode='decrypt')

    dec_path = os.path.join(UPLOAD_FOLDER, 'decrypted_' + file.filename)
    cv2.imwrite(dec_path, decrypted_img)

    return render_template('index.html', decrypted='decrypted_' + file.filename)

if __name__ == '__main__':
    app.run(debug=True)
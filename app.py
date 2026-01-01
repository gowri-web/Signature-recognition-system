import sqlite3
import os
import io
import base64
import numpy as np
import cv2
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIGURATION ---
DATABASE_NAME = 'signature_db.sqlite'
STORAGE_DIR = 'signatures_storage'
# --- FLASK APP SETUP ---
app = Flask(__name__)
CORS(app) 

# --- UTILITIES: DATABASE MANAGEMENT (No Change) ---

def init_db():
    """Initializes the SQLite database with the users table."""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            reference_signature_path TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_reference_to_db(user_id, file_path):
    """Inserts or updates the reference signature path for a user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, reference_signature_path)
        VALUES (?, ?)
    ''', (user_id, file_path))
    conn.commit()
    conn.close()

def get_reference_path(user_id):
    """Retrieves the reference signature path for a user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT reference_signature_path FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# --- UTILITIES: IMAGE PROCESSING (No Change) ---

def base64_to_image(base64_string):
    """Converts a Base64 data URL string (e.g., data:image/png;base64,...) to a CV2 image object."""
    try:
        if ',' in base64_string:
            _, encoded_data = base64_string.split(',', 1)
        else:
            encoded_data = base64_string
            
        np_arr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error decoding base64 to image: {e}")
        return None

def image_to_base64(image):
    """Converts a CV2 image object back to a Base64 PNG data URL string."""
    _, buffer = cv2.imencode('.png', image)
    encoded_string = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{encoded_string}"


# --- SIGNATURE RECOGNITION CORE LOGIC (MODIFIED) ---

def process_signature_images(input_img, reference_img):
    """
    MODIFIED: Performs feature extraction (Hu Moments) and comparison (Euclidean Distance).
    """
    
    def get_features(img):
        """Helper to get pre-processed image and Hu Moments."""
        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 2. Binarize (Separate strokes from background)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 3. Find Contours (the actual signature shape)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, thresh # No signature found

        # 4. Find the largest contour (the main signature stroke)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # 5. Calculate Hu Moments (7 shape features)
        moments = cv2.moments(largest_contour)
        hu_moments = cv2.HuMoments(moments).flatten()
        # Convert to log scale for better comparison and stability
        log_hu_moments = -np.sign(hu_moments) * np.log10(np.abs(hu_moments))
        
        return log_hu_moments, gray

    # --- Feature Extraction ---
    input_features, gray_input = get_features(input_img)
    reference_features, gray_ref = get_features(reference_img)
    
    if input_features is None or reference_features is None:
        return {
            "recognitionResult": "ERROR: Signature contour not detected in one or both images.",
            "entropy": "N/A", "mean": "N/A", "grayConversionB64": None,
            "filteredImageB64": None, "roiInputB64": None, "roiRefB64": None,
        }
        
    # --- Verification Logic (Euclidean Distance of Hu Moments) ---
    
    # Calculate Euclidean distance (the difference in shape features)
    hu_distance = np.linalg.norm(input_features - reference_features)
    
    # IMPORTANT: This threshold needs tuning for real-world use. 
    # Smaller distance means higher similarity.
    ACCEPTANCE_THRESHOLD = 0.8 # A starting point for demonstration

    # Prepare data for frontend display
    roi_size = (150, 75)
    roi_input = cv2.resize(gray_input, roi_size, interpolation=cv2.INTER_AREA)
    roi_ref = cv2.resize(gray_ref, roi_size, interpolation=cv2.INTER_AREA)
    
    # Use distance for 'Entropy' and the first Hu moment for 'Mean' (for display only)
    display_entropy = hu_distance 
    display_mean = input_features[0] 

    if hu_distance < ACCEPTANCE_THRESHOLD:
        recognition_result = f"ACCEPTED (Distance: {hu_distance:.4f})"
    else:
        recognition_result = f"REJECTED (Distance: {hu_distance:.4f})"
        
    
    return {
        "recognitionResult": recognition_result,
        "entropy": f"{display_entropy:.4f}", # Now displays the Hu Moment Distance
        "mean": f"{display_mean:.4f}",       # Now displays the first Hu Moment
        # Return processed images as Base64 for visualization on the frontend
        "grayConversionB64": image_to_base64(gray_input),
        "filteredImageB64": image_to_base64(gray_input), # Reusing gray for filtered visualization
        "roiInputB64": image_to_base64(roi_input),
        "roiRefB64": image_to_base64(roi_ref),
    }


# --- API ENDPOINTS (No Change) ---

@app.route('/api/save-reference', methods=['POST'])
def save_reference():
    """Endpoint to save a user's reference signature to the file system and DB."""
    data = request.get_json()
    user_id = data.get('userId')
    signature_b64 = data.get('signatureB64')
    if not user_id or not signature_b64: return jsonify({"success": False, "message": "Missing data"}), 400
    try:
        img = base64_to_image(signature_b64)
        file_name = f"{user_id}_reference.png"
        file_path = os.path.join(STORAGE_DIR, file_name)
        cv2.imwrite(file_path, img)
        save_reference_to_db(user_id, file_path)
        return jsonify({"success": True, "message": "Reference signature saved successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {e}"}), 500

@app.route('/api/get-reference', methods=['GET'])
def get_reference():
    """Endpoint to retrieve a user's reference signature from the file system."""
    user_id = request.args.get('userId')
    if not user_id: return jsonify({"success": False, "message": "Missing userId parameter"}), 400
    try:
        file_path = get_reference_path(user_id)
        if not file_path or not os.path.exists(file_path): 
            return jsonify({"success": False, "message": "No reference signature found."}), 404
        img = cv2.imread(file_path)
        signature_b64 = image_to_base64(img)
        return jsonify({"success": True, "signatureB64": signature_b64})
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {e}"}), 500

@app.route('/api/recognize', methods=['POST'])
def recognize():
    """Endpoint to perform the signature recognition and verification."""
    data = request.get_json()
    input_b64 = data.get('input_image_b64')
    reference_b64 = data.get('reference_image_b64')
    if not input_b64 or not reference_b64: return jsonify({"error": "Missing image data"}), 400
    try:
        input_img = base64_to_image(input_b64)
        reference_img = base64_to_image(reference_b64)
        results = process_signature_images(input_img, reference_img)
        return jsonify(results)
    except Exception as e:
        print(f"Recognition error: {e}")
        return jsonify({"error": f"An error occurred during recognition: {e}"}), 500

# --- RUN SERVER ---

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=8080, debug=True)
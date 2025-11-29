# app.py (Flask/Python) - ĐÃ FIX LỖI JSON DECODE

from flask import Flask, render_template, request, jsonify
import requests
from flask_wtf import FlaskForm 
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- CẤU HÌNH BAN ĐẦU ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mot_khoa_bi_mat_rat_manh_me_123' 

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"] 
)

# --- ROUTE PHỤC VỤ HTML ---
@app.route('/')
@limiter.limit("20 per minute", methods=['GET']) 
def index():
    return render_template('index.html')

# --- ROUTE PROXY (CHUYỂN TIẾP YÊU CẦU GIẢI MÃ) ---
@app.route('/api/giai-ma', methods=['POST'])
@limiter.limit("20 per minute") 
def proxy_giai_ma():
    # 1. Định nghĩa URL của API giải mã bên ngoài (Backend Node.js/Express)
    EXTERNAL_API_URL = "https://doraemon-backend.onrender.com/giai-ma"

    # 2. Lấy dữ liệu JSON từ yêu cầu của người dùng
    data = request.get_json() 
    if data is None:
        return jsonify({"error": "Dữ liệu JSON không hợp lệ."}), 400

    try:
        # 3. Chuyển tiếp (Proxy) yêu cầu POST này đến API bên ngoài
        response = requests.post(
            EXTERNAL_API_URL, 
            json={
                "userInput": data.get('userInput'),
                "recaptchaToken": data.get('recaptchaToken'),
                "visitorId": data.get('visitorId')
            }, 
            headers={'Content-Type': 'application/json'}
        )
        
        # 4. BẮT LỖI QUAN TRỌNG: Kiểm tra và xử lý phản hồi không phải JSON
        if response.content:
            try:
                # Nếu có nội dung, cố gắng parse JSON
                return jsonify(response.json()), response.status_code
            except requests.exceptions.JSONDecodeError:
                # Nếu không thể parse JSON (ví dụ: phản hồi là HTML/text/rỗng nhưng có mã lỗi)
                # Đây là lỗi từ Backend Node.js của bạn, không gửi JSON như mong đợi.
                print(f"Lỗi phân tích JSON từ API ngoài. Mã trạng thái: {response.status_code}")
                # Trả về thông báo lỗi chung kèm mã trạng thái gốc
                return jsonify({
                    "error": f"Lỗi từ máy chủ giải mã (Code {response.status_code}). Phản hồi không phải JSON."
                }), response.status_code
        else:
            # Xử lý trường hợp API ngoài trả về mã trạng thái OK/204 nhưng không có nội dung
            if response.status_code == 204:
                return jsonify({}), 204 
            else:
                return jsonify({
                    "error": f"Lỗi từ máy chủ giải mã (Code {response.status_code}). Không có dữ liệu phản hồi."
                }), response.status_code
        
    except requests.exceptions.RequestException as e:
        # Xử lý lỗi nếu không kết nối được với API bên ngoài (Timeout, DNS error, v.v.)
        print(f"Lỗi khi kết nối đến API ngoài: {e}")
        return jsonify({"error": "Proxy lỗi: Không thể kết nối đến máy chủ giải mã. Vui lòng thử lại."}), 503 

# --- CHẠY ỨNG DỤNG ---
if __name__ == '__main__':
    app.run(debug=True)
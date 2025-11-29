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
    EXTERNAL_API_URL = "https://doraemon-backend.onrender.com/giai-ma"

    data = request.get_json() 
    if data is None:
        return jsonify({"error": "Dữ liệu JSON không hợp lệ."}), 400

    try:
        response = requests.post(
            EXTERNAL_API_URL, 
            json={
                "userInput": data.get('userInput'),
                "recaptchaToken": data.get('recaptchaToken'),
                "visitorId": data.get('visitorId')
            }, 
            headers={'Content-Type': 'application/json'}
        )
        
        # --- BƯỚC SỬA LỖI QUAN TRỌNG: XỬ LÝ PHẢN HỒI KHÔNG PHẢI JSON ---
        # Kiểm tra xem có nội dung phản hồi hay không
        if response.content:
            try:
                # Nếu có nội dung, cố gắng parse JSON
                return jsonify(response.json()), response.status_code
            except requests.exceptions.JSONDecodeError:
                # Nếu không thể parse JSON (ví dụ: phản hồi là HTML/text/rỗng nhưng có mã lỗi)
                print(f"Lỗi phân tích JSON từ API ngoài. Mã trạng thái: {response.status_code}, Nội dung: {response.text[:100]}...")
                # Trả về lỗi server hoặc thông báo tùy thuộc vào mã trạng thái
                if response.status_code >= 400:
                     return jsonify({"error": f"Lỗi từ máy chủ giải mã (Code {response.status_code}): Phản hồi không phải JSON hợp lệ."}), response.status_code
                else:
                     return jsonify({"error": "Lỗi không xác định: Phản hồi từ API ngoài không hợp lệ."}), 500
        else:
            # Xử lý trường hợp API ngoài trả về mã trạng thái OK (200, 204, etc.) nhưng không có nội dung
            print(f"API ngoài trả về mã {response.status_code} nhưng không có nội dung.")
            if response.status_code == 204:
                return jsonify({}), 204 # Trả về 204 nếu không có nội dung (No Content)
            else:
                return jsonify({"message": f"Yêu cầu thành công (Code {response.status_code}), nhưng API ngoài không trả về dữ liệu."}), response.status_code
        
    except requests.exceptions.RequestException as e:
        # Xử lý lỗi nếu không kết nối được với API bên ngoài (Timeout, DNS error, v.v.)
        print(f"Lỗi khi kết nối đến API ngoài: {e}")
        return jsonify({"error": "Proxy lỗi: Không thể kết nối đến máy chủ giải mã. Vui lòng thử lại."}), 503 

# --- CHẠY ỨNG DỤNG ---
if __name__ == '__main__':
    app.run(debug=True)

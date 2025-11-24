from flask import Flask, render_template, request, jsonify
import requests
# Thư viện Flask-WTF cần thiết cho Form (dù không sử dụng trong code hiện tại, nhưng giữ để tránh lỗi import)
from flask_wtf import FlaskForm 
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- CẤU HÌNH BAN ĐẦU ---
app = Flask(__name__)
# Đảm bảo có SECRET_KEY để Flask-WTF và các tính năng bảo mật khác hoạt động
app.config['SECRET_KEY'] = 'mot_khoa_bi_mat_rat_manh_me_123' 

# Khởi tạo Flask-Limiter
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"] # Giới hạn mặc định chung
)

# --- ROUTE PHỤC VỤ HTML ---
@app.route('/')
# ĐÃ SỬA: Giới hạn 20 yêu cầu/phút cho trang chính (GET) để tránh lỗi 429
@limiter.limit("20 per minute", methods=['GET']) 
def index():
    # Flask sẽ tự động tìm file index.html trong thư mục 'templates'
    return render_template('index.html')

# --- ROUTE PROXY (CHUYỂN TIẾP YÊU CẦU GIẢI MÃ) ---
@app.route('/api/giai-ma', methods=['POST'])
# Áp dụng giới hạn tốc độ cho API giải mã (có thể thay đổi tùy ý)
@limiter.limit("20 per minute") 
def proxy_giai_ma():
    # 1. Định nghĩa URL của API giải mã bên ngoài
    EXTERNAL_API_URL = "https://doraemon-backend.onrender.com/giai-ma"

    # 2. Lấy dữ liệu JSON từ yêu cầu của người dùng
    data = request.get_json() 
    if data is None:
        return jsonify({"error": "Dữ liệu JSON không hợp lệ."}), 400

    try:
        # 3. Chuyển tiếp (Proxy) yêu cầu POST này đến API bên ngoài
        # LƯU Ý: Đổi tên trường dữ liệu để khớp với backend của bạn (nếu cần)
        response = requests.post(
            EXTERNAL_API_URL, 
            json={
                "userInput": data.get('userInput'),
                "recaptchaToken": data.get('recaptchaToken'),
                "visitorId": data.get('visitorId')
            }, 
            headers={'Content-Type': 'application/json'}
        )
        
        # 4. Trả về kết quả từ API bên ngoài cho trình duyệt người dùng
        # Chuyển đổi phản hồi (response) thành JSON và giữ lại mã trạng thái HTTP gốc
        return jsonify(response.json()), response.status_code
        
    except requests.exceptions.RequestException as e:
        # Xử lý lỗi nếu không kết nối được với API bên ngoài
        print(f"Lỗi khi kết nối đến API ngoài: {e}")
        return jsonify({"error": "Proxy lỗi: Không thể kết nối đến máy chủ giải mã."}), 503 

# --- CHẠY ỨNG DỤNG ---
if __name__ == '__main__':
    # Chạy trên môi trường cục bộ
    app.run(debug=True)
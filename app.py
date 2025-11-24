from flask import Flask, render_template, request, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Khởi tạo ứng dụng Flask
app = Flask(__name__)

# Thiết lập một khóa bí mật (Secret Key) là BẮT BUỘC cho Flask-WTF và Flash messages
app.config['SECRET_KEY'] = 'mot_khoa_bi_mat_rat_manh_me_123'

# Khởi tạo Flask-Limiter
# Sử dụng địa chỉ IP của client để xác định giới hạn
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"] # Giới hạn mặc định
)

# Định nghĩa Form sử dụng Flask-WTF
class SimpleForm(FlaskForm):
    # Trường Tên, yêu cầu dữ liệu và giới hạn độ dài
    name = StringField('Tên của bạn', validators=[DataRequired(), Length(min=2, max=30)])
    submit = SubmitField('Gửi')

# Định nghĩa Route chính
@app.route('/', methods=['GET', 'POST'])
# Áp dụng giới hạn tốc độ chỉ cho route này
@limiter.limit("5 per minute") 
def index():
    form = SimpleForm()
    
    # Xử lý khi Form được gửi đi (POST) và hợp lệ
    if form.validate_on_submit():
        # Lấy dữ liệu từ form
        user_name = form.name.data
        
        # Hiển thị thông báo thành công
        flash(f'Chào mừng, {user_name}! Dữ liệu đã được gửi thành công.', 'success')
        
        # Chuyển hướng về trang chủ (tránh gửi lại form khi refresh)
        return redirect(url_for('index'))
        
    # Xử lý khi truy cập trang (GET) hoặc Form không hợp lệ
    return render_template('index.html', form=form)

# Định nghĩa Route bị giới hạn tốc độ nghiêm ngặt hơn
@app.route('/test_limit')
@limiter.limit("2 per minute")
def test_limit():
    return "Bạn chỉ có thể truy cập trang này 2 lần mỗi phút!"

if __name__ == '__main__':
    app.run(debug=True)
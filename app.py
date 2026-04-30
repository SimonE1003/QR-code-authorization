from flask import Flask, request,render_template, session, redirect
import pymysql
from datetime import datetime, timedelta
import qrcode
import io
import base64
import os

def init_db():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # 创建 certifications 表（如果不存在）
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS certifications (
                    id INT NOT NULL AUTO_INCREMENT,
                    rednote_id VARCHAR(255) NOT NULL UNIQUE,
                    account_name VARCHAR(255) NOT NULL,
                    cert_code VARCHAR(50) NOT NULL UNIQUE,
                    valid_from DATETIME NOT NULL,
                    valid_to DATETIME NOT NULL,
                    status ENUM('active', 'expired') DEFAULT 'active',
                    PRIMARY KEY (id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            ''')
        conn.commit()
        conn.close()

# 数据库连接工具函数
def get_db_connection():
    conn = pymysql.connect(** DB_CONFIG)
    return conn

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL 数据库配置
DB_CONFIG = {
    'host': 'localhost',  # 本地测试用localhost；云服务器填服务器IP
    'user': 'root',       # MySQL用户名（默认root）
    'password': 'Wym:050311',  
    'database': 'midjourney_cert',  # 数据库名
    'port': 3306,
    'charset': 'utf8mb4'
}

#储存用户名和密码!!!
users = {
    "user1": "password1",
    "user2": "password2"
}

# 确保二维码图片存储目录存在
QR_CODE_FOLDER = 'static/qrcodes'
os.makedirs(QR_CODE_FOLDER, exist_ok=True)


# 登录页面路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            session['username'] = username
            return redirect('/')
        else:
            return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')


# 登出路由
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

# 1. 显示表单页面
@app.route('/')
def show_form():
    if 'username' in session:
        return render_template('form.html', username=session['username'])
    return render_template('login.html')

# 2. 处理表单提交并生成二维码
@app.route('/generate', methods=['POST'])
def generate_cert():
    init_db()
    # 获取表单数据
    rednote_id = request.form.get('rednote_id')
    account_name = request.form.get('account_name')
    valid_days = int(request.form.get('valid_days', 365))
    
    # 验证表单数据
    if not rednote_id or not account_name:
        return render_template('form.html', error="请填写完整的小红书ID和账号名称")
    
    # 生成认证编号：品牌前缀 + 日期 + 随机3位数
    today = datetime.now().strftime("%Y%m%d")
    random_num = os.urandom(2).hex()  # 生成更随机的4位16进制数（避免重复）
    cert_code = f"MJ-{today}-{random_num}"
    
    # 计算有效期
    valid_from = datetime.now()
    valid_to = valid_from + timedelta(days=valid_days)
    valid_from_str = valid_from.strftime("%Y-%m-%d")
    valid_to_str = valid_to.strftime("%Y-%m-%d")
    
    # 存入数据库
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO certifications 
            (rednote_id, account_name, cert_code, valid_from, valid_to, status) 
            VALUES (%s, %s, %s, %s, %s, 'active')
            """
            cursor.execute(sql, (
                rednote_id,
                account_name,
                cert_code,
                valid_from.strftime("%Y-%m-%d %H:%M:%S"),
                valid_to.strftime("%Y-%m-%d %H:%M:%S")
            ))
        conn.commit()
        conn.close()
        
    except pymysql.MySQLError as e:
        return render_template('form.html', error=f"数据库错误：{str(e)}")
    
    # 生成二维码（内存中生成，转为base64）
    try:
        # 生成验证链接（替换为你的服务器IP或域名）
        verify_url = f"https://593eb15804b8.ngrok-free.app/verify?code={cert_code}" 
        
        # 创建二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转为base64编码（用于HTML显示）
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        qr_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        
        # 渲染成功页面，传递数据到模板
        return render_template(
            'success.html',
            rednote_id=rednote_id,
            account_name=account_name,
            cert_code=cert_code,
            valid_from=valid_from_str,
            valid_to=valid_to_str,
            qr_base64=qr_base64
        )
    
    except Exception as e:
        return render_template('form.html', error=f"生成二维码失败：{str(e)}")

# 3. 扫码验证接口
@app.route('/verify', methods=['GET'])
def verify():
    cert_code = request.args.get('code')
    if not cert_code:
        return render_template('verify_fail.html', message="无效的二维码或认证编号")
    
    try:
        # 查询数据库
        conn = get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM certifications 
                WHERE cert_code = %s AND status = 'active'
            """, (cert_code,))
            cert = cursor.fetchone()
        conn.close()
        
        # 验证结果处理
        if not cert:
            return render_template('verify_fail.html', message="该认证不存在或已被撤销")
        
        # 检查有效期
        if datetime.now() > cert['valid_to']:
            # 更新状态为过期
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE certifications SET status = 'expired' 
                    WHERE cert_code = %s
                """, (cert_code,))
            conn.commit()
            conn.close()
            return render_template('verify_fail.html', message="该认证已过期")
        
        # 验证成功
        return render_template('verify_success.html', cert=cert)
    
    except pymysql.MySQLError as e:
        return render_template('verify_fail.html', message=f"验证过程出错：{str(e)}")

# 启动服务
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
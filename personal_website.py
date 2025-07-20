import sqlite3
import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from pathlib import Path

app = Flask(__name__)

# 从环境变量读取配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-2025')
PORT = int(os.environ.get('PORT', 5000))
DB_PATH = os.environ.get('DB_PATH', str(Path(__file__).parent / 'messages.db'))
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')

# 初始化 SQLite 数据库
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      sender_name TEXT NOT NULL,
                      message TEXT NOT NULL)''')
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Database error during init: {e}")
        return False
    finally:
        conn.close()
    return True

# 内存存储（仅在数据库失败时使用）
messages = []

if not init_db():
    print("Falling back to in-memory storage due to database error.")

# HTML 模板（包含导航、表单、作品集等）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>个人主页</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #eceff1;
        }
        .nav {
            background-color: #1a237e;
            padding: 10px;
            border-radius: 8px;
        }
        .nav a {
            color: white;
            margin-right: 20px;
            text-decoration: none;
            font-weight: 700;
        }
        .nav a:hover {
            color: #00bcd4;
        }
        .header {
            text-align: center;
            padding: 30px;
            background-color: #1a237e;
            color: white;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .content {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        .main-content {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .sidebar {
            background-color: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
        }
        .contact-info, .portfolio, .edit-profile {
            margin-top: 20px;
            padding: 15px;
            background-color: #e0f7fa;
            border-radius: 8px;
        }
        .form-container {
            margin-top: 20px;
            padding: 15px;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .form-container input, .form-container textarea {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #b0bec5;
            border-radius: 4px;
        }
        .form-container button, .delete-btn {
            padding: 10px 20px;
            background-color: #00bcd4;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .form-container button:hover, .delete-btn:hover {
            background-color: #00838f;
        }
        .messages {
            margin-top: 20px;
        }
        .message {
            padding: 10px;
            margin: 5px 0;
            background-color: #e0f7fa;
            border-left: 4px solid #00bcd4;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .social-icons img {
            width: 24px;
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="nav">
        <a href="{{ url_for('home') }}">主页</a>
        <a href="{{ url_for('about') }}">关于</a>
    </div>
    <div class="header">
        <h1>{{ name }}</h1>
        <h3>{{ title }}</h3>
    </div>
    <div class="content">
        <div class="main-content">
            <h2>关于我</h2>
            <p>{{ about }}</p>
            <h2>技能</h2>
            <ul>
                {% for skill in skills %}
                <li>{{ skill }}</li>
                {% endfor %}
            </ul>
            <div class="portfolio">
                <h2>作品集</h2>
                {% for project in portfolio %}
                <div>
                    <strong>{{ project.title }}</strong>: {{ project.description }}
                </div>
                {% endfor %}
            </div>
            <div class="form-container">
                <h2>留言</h2>
                <form method="POST" action="{{ url_for('home') }}">
                    <input type="text" name="sender_name" placeholder="您的姓名" required>
                    <textarea name="message" placeholder="您的留言" rows="4" required></textarea>
                    <button type="submit">提交</button>
                </form>
            </div>
            <div class="messages">
                <h2>留言列表</h2>
                {% if messages %}
                    {% for msg in messages %}
                    <div class="message">
                        <span><strong>{{ msg.sender_name }}:</strong> {{ msg.message }}</span>
                        <form method="POST" action="{{ url_for('delete_message', msg_id=msg.id) }}">
                            <button class="delete-btn" type="submit">删除</button>
                        </form>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>暂无留言。</p>
                {% endif %}
            </div>
        </div>
        <div class="sidebar">
            <div class="contact-info">
                <h2>联系方式</h2>
                <p>邮箱: {{ email }}</p>
                <p>LinkedIn: <a href="{{ linkedin }}">{{ linkedin }}</a></p>
                <p class="social-icons">
                    <a href="{{ twitter }}"><img src="https://img.icons8.com/ios-filled/50/ffffff/twitterx.png" alt="Twitter/X"></a>
                    <a href="{{ github }}"><img src="https://img.icons8.com/ios-filled/50/ffffff/github.png" alt="GitHub"></a>
                </p>
            </div>
            <div class="edit-profile">
                <h2>编辑个人信息</h2>
                <form method="POST" action="{{ url_for('edit_profile') }}">
                    <input type="text" name="name" placeholder="姓名" value="{{ name }}" required>
                    <input type="text" name="title" placeholder="职业" value="{{ title }}" required>
                    <textarea name="about" placeholder="关于我" rows="4">{{ about }}</textarea>
                    <button type="submit">更新</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

# 关于页面模板
ABOUT_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>关于我</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #eceff1;
        }
        .nav {
            background-color: #1a237e;
            padding: 10px;
            border-radius: 8px;
        }
        .nav a {
            color: white;
            margin-right: 20px;
            text-decoration: none;
            font-weight: 700;
        }
        .nav a:hover {
            color: #00bcd4;
        }
        .header {
            text-align: center;
            padding: 30px;
            background-color: #1a237e;
            color: white;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .main-content {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <div class="nav">
        <a href="{{ url_for('home') }}">主页</a>
        <a href="{{ url_for('about') }}">关于</a>
    </div>
    <div class="header">
        <h1>关于 {{ name }}</h1>
    </div>
    <div class="main-content">
        <h2>我的故事</h2>
        <p>{{ about }}</p>
        <h2>联系方式</h2>
        <p>邮箱: {{ email }}</p>
        <p>LinkedIn: <a href="{{ linkedin }}">{{ linkedin }}</a></p>
        <p class="social-icons">
            <a href="{{ twitter }}"><img src="https://img.icons8.com/ios-filled/50/ffffff/twitterx.png" alt="Twitter/X"></a>
            <a href="{{ github }}"><img src="https://img.icons8.com/ios-filled/50/ffffff/github.png" alt="GitHub"></a>
        </p>
    </div>
</body>
</html>
"""

# 个人信息（可通过编辑表单更新）
profile = {
    'name': '你的名字',
    'title': '软件开发者',
    'about': '我是一名热爱编程的软件开发者，擅长使用 Python 和其他现代技术构建 Web 应用。',
    'skills': ['Python', 'JavaScript', 'HTML/CSS', 'Flask'],
    'email': 'your.email@example.com',
    'linkedin': 'https://www.linkedin.com/in/your-profile',
    'twitter': 'https://twitter.com/your-profile',
    'github': 'https://github.com/your-profile',
    'portfolio': [
        {'title': '项目一', 'description': '一个使用 Flask 开发的个人网页应用'},
        {'title': '项目二', 'description': '基于 React 的前端项目'}
    ]
}

# 简单权限检查（需扩展为完整认证）
def is_authorized():
    return session.get('logged_in', False)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        sender_name = request.form.get('sender_name')
        message = request.form.get('message')
        if sender_name and message:
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO messages (sender_name, message) VALUES (?, ?)", (sender_name, message))
                conn.commit()
            except sqlite3.Error as e:
                print(f"Database insert error: {e}")
                if 'messages' not in globals():
                    messages.append({'sender_name': sender_name, 'message': message})
            finally:
                conn.close()
        return redirect(url_for('home'))

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, sender_name, message FROM messages")
        messages = [{'id': row[0], 'sender_name': row[1], 'message': row[2]} for row in c.fetchall()]
    except sqlite3.Error as e:
        print(f"Database select error: {e}")
        messages = messages if 'messages' in globals() else []
    finally:
        conn.close()

    context = profile.copy()
    context['messages'] = messages
    return render_template_string(HTML_TEMPLATE, **context)

@app.route('/delete/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    if not is_authorized():
        return redirect(url_for('home'))  # 未授权用户无法删除
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database delete error: {e}")
        if 'messages' in globals():
            messages[:] = [msg for msg in messages if msg.get('id') != msg_id]
    finally:
        conn.close()
    return redirect(url_for('home'))

@app.route('/edit', methods=['POST'])
def edit_profile():
    if not is_authorized():
        return redirect(url_for('home'))  # 未授权用户无法编辑
    profile['name'] = request.form.get('name', profile['name'])
    profile['title'] = request.form.get('title', profile['title'])
    profile['about'] = request.form.get('about', profile['about'])
    return redirect(url_for('home'))

@app.route('/about')
def about():
    context = profile.copy()
    return render_template_string(ABOUT_TEMPLATE, **context)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
from flask import Flask, render_template, request, jsonify, redirect
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
import os

from werkzeug.security import generate_password_hash, check_password_hash

import re
import random
import datetime  # ログのタイムスタンプに使用


app = Flask(__name__, static_url_path='/static')


# サインアップ・ログイン機能
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
app.config['SECRET_KEY'] = os.urandom(24)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(12))

class ChatLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='chat_logs')
    message = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# チャットボット機能
# パターンファイルのパス
pattern_file_path = 'pattern.txt'

def load_patterns(pattern_file_path):
    patterns = []
    with open(pattern_file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                # パターンと応答を分割して取得
                pattern, responses = line.split('->')
                pattern = pattern.strip()  # パターンの前後の空白を削除
                responses = [response.strip() for response in responses.split(',')]  # 応答をリストに分割して格納
                patterns.append({
                    'pattern': pattern,
                    'responses': responses
                })
    return patterns

# パターンと応答を読み込む
patterns = load_patterns(pattern_file_path)

def write_chat_log(log_filename,  user_message, bot_response):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_filename, 'a', encoding='utf-8') as file:
        file.write(f"{timestamp}\n")
        file.write(f"User: {user_message}\n")
        file.write(f"Bot: {bot_response}\n")
        file.write("\n")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/mode')
@login_required
def mode():
    return render_template("mode.html")

@app.route("/signup",  methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User(username=username, password=generate_password_hash(password, method='sha256'))

        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    else:
        return render_template("signup.html")
    
@app.route("/login",  methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect('/mode')
        # 例外処理

    else:
        return render_template("login.html")
        
@app.route("/logout",  methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect('/login')

# チャットメッセージを保持するリスト
chat_messages_normal = []
chat_messages_polite = []
chat_messages_pyon = []
chat_messages_kao = []
chat_messages_exclamation = []

@app.route('/normal', methods=['GET', 'POST'])
@login_required
def normal_page():
    chat_messages = []  # チャットメッセージを保持するリスト
    if request.method == 'POST':
        
        user_message = request.form['message']

        # パターンに対する応答を生成
        response = normal_response(user_message, patterns)

        # チャットログをデータベースに保存
        chat_log = ChatLog(user=current_user, message=user_message)
        db.session.add(chat_log)
        db.session.commit()

        # メッセージをチャットメッセージリストに追加
        chat_messages_normal.append({'user': user_message, 'bot': response})

        # チャットログとしてファイルに書き込む
        write_chat_log('normal.txt', user_message, response)
    user_name = current_user.username
    return render_template('normal.html', chat_messages=chat_messages_normal, user_name=user_name)

# ユーザーの入力に応じた応答を生成する関数
def normal_response(user_message, patterns):
    for pattern in patterns:
        match = re.search(pattern['pattern'], user_message)
        if match:
            responses = pattern['responses']
            response = random.choice(responses)  # 応答をランダムに選択
            if '%s' in response and match.groups():
                response = response % match.group(1)  # 応答内の %s をマッチしたグループで置換
            return response
    return "どういう意味？"

@app.route('/polite', methods=['GET', 'POST'])
@login_required
def polite_page():
    chat_messages = []  # チャットメッセージを保持するリスト
    if request.method == 'POST':
        user_message = request.form['message']

        # パターンに対する応答を生成
        response = polite_response(user_message, patterns)

        # チャットログをデータベースに保存
        chat_log = ChatLog(user=current_user, message=user_message)
        db.session.add(chat_log)
        db.session.commit()

        # メッセージをチャットメッセージリストに追加
        chat_messages_polite.append({'user': user_message, 'bot': response})

        # チャットログとしてファイルに書き込む
        write_chat_log('polite.txt', user_message, response)
    user_name = current_user.username
    return render_template('polite.html', chat_messages=chat_messages_polite, user_name=user_name)

# ユーザーの入力に応じた応答を生成する関数
def polite_response(user_message, patterns):
    for pattern in patterns:
        match = re.search(pattern['pattern'], user_message)
        if match:
            responses = pattern['responses']
            response = random.choice(responses)  # 応答をランダムに選択
            if '%s' in response and match.groups():
                response = response % match.group(1)  # 応答内の %s をマッチしたグループで置換

            # 「。」を「です。」に置換
            response = response.replace('。', 'です。')
            # 「？」を「ですか？」に置換
            response = response.replace('？', 'ですか？')

            return response
    return "なんと申しました？"

@app.route('/pyon', methods=['GET', 'POST'])
@login_required
def pyon_page():
    chat_messages = []  # チャットメッセージを保持するリスト
    if request.method == 'POST':
        user_message = request.form['message']

        # パターンに対する応答を生成
        response = pyon_response(user_message, patterns)

        # チャットログをデータベースに保存
        chat_log = ChatLog(user=current_user, message=user_message)
        db.session.add(chat_log)
        db.session.commit()

        # メッセージをチャットメッセージリストに追加
        chat_messages_pyon.append({'user': user_message, 'bot': response})

        # チャットログとしてファイルに書き込む
        write_chat_log('pyon.txt', user_message, response)
    user_name = current_user.username
    return render_template('pyon.html', chat_messages=chat_messages_pyon, user_name=user_name)

# ユーザーの入力に応じた応答を生成する関数
def pyon_response(user_message, patterns):
    for pattern in patterns:
        match = re.search(pattern['pattern'], user_message)
        if match:
            responses = pattern['responses']
            response = random.choice(responses)  # 応答をランダムに選択
            if '%s' in response and match.groups():
                response = response % match.group(1)  # 応答内の %s をマッチしたグループで置換

            # 応答文の文中に「。」がある場合は「だぴょん。」に置き換える
            response = response.replace('。', 'だぴょん。')
            # 応答文に「？」がある場合は「だぴょんか？」に置き換える
            response = response.replace('？', 'だぴょんか？')

            return response
    return "なんと言ったぴょんか？"

@app.route('/kao', methods=['GET', 'POST'])
@login_required
def kao_page():
    chat_messages = []  # チャットメッセージを保持するリスト
    if request.method == 'POST':
        user_message = request.form['message']

        # パターンに対する応答を生成
        response = kao_response(user_message, patterns)

        # チャットログをデータベースに保存
        chat_log = ChatLog(user=current_user, message=user_message)
        db.session.add(chat_log)
        db.session.commit()

        # メッセージをチャットメッセージリストに追加
        chat_messages_kao.append({'user': user_message, 'bot': response})

        # チャットログとしてファイルに書き込む
        write_chat_log('kao.txt', user_message, response)
    user_name = current_user.username
    return render_template('kao.html', chat_messages=chat_messages_kao, user_name=user_name)

# ユーザーの入力に応じた応答を生成する関数
def kao_response(user_message, patterns):
    for pattern in patterns:
        match = re.search(pattern['pattern'], user_message)
        if match:
            responses = pattern['responses']
            response = random.choice(responses)  # 応答をランダムに選択
            if '%s' in response and match.groups():
                response = response % match.group(1)  # 応答内の %s をマッチしたグループで置換

            # 応答文の文中に「。」がある場合はランダムに顔文字に置き換える
            response = replace_dot(response)
            # 応答文に「？」がある場合はランダムに顔文字に置き換える
            response = replace_question(response)

            return response
    return "もう少し分かりやすく教えて(>_<)"

# 文中の「。」をランダムに置き換える関数
def replace_dot(sentence):
    # 置き換える顔文字のリスト
    kaomoji_list = ["(^^) ", "(-_-) ", "(^-^) ", "\(^^)/ ", "\(^o^)/ ", "(^_^) "]
    # 文章内の「。」をランダムに選んだ顔文字で置き換える
    replaced_sentence = re.sub(r'。', lambda _: random.choice(kaomoji_list), sentence)
    return replaced_sentence

# 文中の「？」をランダムに置き換える関数
def replace_question(sentence):
    # 置き換える顔文字のリスト
    kaomoji_list = ["？(?_?) ", "？(>_<) ","？(゜_゜) ","？(・_・?) ", "？(^^; "]
    # 文章内の「？」をランダムに選んだ顔文字で置き換える
    replaced_sentence = re.sub(r'？', lambda _: random.choice(kaomoji_list), sentence)
    return replaced_sentence

@app.route('/exclamation', methods=['GET', 'POST'])
@login_required
def exclamation_page():
    chat_messages = []  # チャットメッセージを保持するリスト
    if request.method == 'POST':
        user_message = request.form['message']

        # パターンに対する応答を生成
        response = exclamation_response(user_message, patterns)

        # チャットログをデータベースに保存
        chat_log = ChatLog(user=current_user, message=user_message)
        db.session.add(chat_log)
        db.session.commit()

        # メッセージをチャットメッセージリストに追加
        chat_messages_exclamation.append({'user': user_message, 'bot': response})

        # チャットログとしてファイルに書き込む
        write_chat_log('exclamation.txt', user_message, response)
    user_name = current_user.username
    return render_template('exclamation.html', chat_messages=chat_messages_exclamation, user_name=user_name)

# ユーザーの入力に応じた応答を生成する関数
def exclamation_response(user_message, patterns):
    for pattern in patterns:
        match = re.search(pattern['pattern'], user_message)
        if match:
            responses = pattern['responses']
            response = random.choice(responses)  # 応答をランダムに選択
            if '%s' in response and match.groups():
                response = response % match.group(1)  # 応答内の %s をマッチしたグループで置換

            # 応答文の文中に「。」がある場合は「！！！」に置き換える                
            response = response.replace('。', '！！')
            # 応答文に「？」がある場合は「！？」に置き換える
            response = response.replace('？', '！？')

            return response
    return "もう一度おしえて！！"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
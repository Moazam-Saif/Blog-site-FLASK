import base64
import datetime
import os

from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import date
import json
from bs4 import BeautifulSoup

with open("config.json", 'r') as f:
    config = json.load(f)

params = config['params']
local_server = params['local_server']
app = Flask(__name__)
app.secret_key = "super secret key"
app.config['UPLOAD_FOLDER'] = params["uploader_path"]
if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db = SQLAlchemy(app)


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Sr = db.Column(db.Integer, unique=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)  # nullable is true by default
    slug = db.Column(db.String(301), nullable=False)
    img_file = db.Column(db.String(500), nullable=True, default='default.png')
    edited = db.Column(db.DateTime, nullable=True)

with app.app_context():
    db.create_all()


@app.route('/')
def home():
    posts = Posts.query.order_by(desc(Posts.date)).all()
    return render_template('home.html', posts=posts, limit=params['limit_for_home'], current_post="")


@app.route('/post/<string:post_slug>', methods=['GET'])
def post(post_slug):
    posts = Posts.query.filter_by().all()
    post = Posts.query.filter_by(slug=post_slug).first_or_404()
    return render_template('post.html', posts=posts, post=post, limit=params['limit_for_post'], current_post=post.title)


@app.route('/admin-login-dashboard', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if username == params['user'] and password == params['pass']:
            session['admin'] = username
            return redirect('/admin-dashboard-logged-in')
    else:
        return render_template("login.html")



@app.route('/admin-dashboard-logged-in')
def dashboard():
    if 'admin' in session and session['admin'] == params['user']:
        posts = Posts.query.all()
        return render_template("dashboard_new.html", posts=posts, post="")
    else:
        return redirect('/admin-login-dashboard')


@app.route('/edit/<string:post_slug>', methods=['GET', 'POST'])
def edit(post_slug):
    if 'admin' in session and session['admin'] == params['user']:
        post = Posts.query.filter_by(slug=post_slug).first_or_404()
        img_file_name = post.img_file
        if request.method == 'POST':
            img = request.files['img_file']
            img_name = secure_filename(img.filename)
            ext = ('.jpeg', '.png', '.gif', '.jpg')
            if img_name.endswith(ext):
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_name))
                img_file_name = img_name
            post.title = request.form.get('title')
            post.content = request.form['quill_html_content']
            post.img_file = img_file_name
            # post.author = request.form.get('author')
            post.slug = "-" + (post.title).replace(" ", "-")
            post.edited = datetime.datetime.now()
            print(post.edited)
            db.session.commit()
            return redirect('/edit/' + post.slug)
        else:
            return render_template('edit.html', post=post, parameters=params)
    else:
        return redirect('/admin-login-dashboard')


@app.route('/add_post', methods=['GET', 'POST'])
def add():
    if request.method == "POST":
        title = request.form.get('title')
        if not title:  # Handle missing title
            return "Error: Title is required", 400
        content = request.form.get('content')
        author = "Moazam"
        img_file = request.form.get('img_file')
        if not img_file:  # If no image is provided, use the default
            img_file = 'default.png'

        slug = "-" + title.replace(" ", "-")
        date =datetime.datetime.now()
        entry = Posts(title=title, content=content, author=author, img_file=img_file, slug=slug, date=date)
        db.session.add(entry)
        db.session.commit()
        return render_template("add.html",parameters=params)
    else:
        return render_template("add.html",parameters=params)


app.run(debug=True)

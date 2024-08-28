from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Налаштування MongoDB
app.config['MONGO_URI'] = 'mongodb+srv://admin:admin@coursework.ww1zt.mongodb.net/course?retryWrites=true&w=majority&appName=coursework'
mongo = PyMongo(app)
db = mongo.db

# Головна сторінка
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Реєстрація користувача
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # Перевірка наявності користувача
        user = mongo.db.users.find_one({'username': username})

        if user:
            flash('Користувач з таким ім\'ям вже існує!')
            return redirect(url_for('register'))

        # Додавання нового користувача
        mongo.db.users.insert_one({
            'username': username,
            'password': hashed_password
        })

        flash('Реєстрація пройшла успішно! Тепер можна увійти.')
        return redirect(url_for('login'))

    return render_template('register.html')

# Вхід користувача
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Перевірка користувача
        user = mongo.db.users.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Невірне ім\'я користувача або пароль!')

    return render_template('login.html')

# Панель користувача
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Отримання курсів, доступних для користувача
    courses = mongo.db.courses.find()
    return render_template('dashboard.html', courses=courses)

# Створення нового курсу
@app.route('/create_course', methods=['POST'])
def create_course():
    if 'username' not in session:
        return redirect(url_for('login'))

    course_name = request.form['course_name']
    course_description = request.form['course_description']

    # Додавання нового курсу
    mongo.db.courses.insert_one({
        'name': course_name,
        'description': course_description,
        'created_by': session['username'],
        'created_at': datetime.datetime.utcnow()
    })

    return redirect(url_for('dashboard'))

# Сторінка курсу
@app.route('/course/<course_id>')
def course(course_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Отримання даних курсу
    course = mongo.db.courses.find_one({'_id': ObjectId(course_id)})
    return render_template('course.html', course=course)

# Створення тесту
@app.route('/create_test/<course_id>', methods=['POST'])
def create_test(course_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    test_name = request.form['test_name']
    questions = request.form.getlist('questions')

    # Додавання нового тесту до курсу
    mongo.db.tests.insert_one({
        'name': test_name,
        'course_id': ObjectId(course_id),
        'questions': questions,
        'created_by': session['username'],
        'created_at': datetime.datetime.utcnow()
    })

    return redirect(url_for('course', course_id=course_id))

# Сторінка тесту
@app.route('/test/<test_id>')
def test(test_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Отримання даних тесту
    test = mongo.db.tests.find_one({'_id': ObjectId(test_id)})
    return render_template('test.html', test=test)

# Адмін панель
@app.route('/admin')
def admin_panel():
    users = list(db.users.find())
    courses = list(db.courses.find())
    tests = list(db.tests.find())
    return render_template('admin.html', users=users, courses=courses, tests=tests)

# Редагування користувача
@app.route('/admin/edit_user/<user_id>', methods=['POST'])
def edit_user(user_id):
    username = request.form['username']
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'username': username}})
    return redirect(url_for('admin_panel'))

# Видалення користувача
@app.route('/admin/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    db.users.delete_one({'_id': ObjectId(user_id)})
    return redirect(url_for('admin_panel'))

# Редагування курсу
@app.route('/admin/edit_course/<course_id>', methods=['POST'])
def edit_course(course_id):
    name = request.form['name']
    description = request.form['description']
    db.courses.update_one({'_id': ObjectId(course_id)}, {'$set': {'name': name, 'description': description}})
    return redirect(url_for('admin_panel'))

# Видалення курсу
@app.route('/admin/delete_course/<course_id>', methods=['POST'])
def delete_course(course_id):
    db.courses.delete_one({'_id': ObjectId(course_id)})
    return redirect(url_for('admin_panel'))

# Вихід з акаунту
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

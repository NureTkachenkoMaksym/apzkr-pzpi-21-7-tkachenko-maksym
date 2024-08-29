from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, abort, send_file
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import datetime
import io

app = Flask(__name__)
app.secret_key = '213123123'

app.config['MONGO_URI'] = 'mongodb+srv://admin:admin@cluster0.ov8yp.mongodb.net/course?retryWrites=true&w=majority&appName=coursesadtests'
mongo = PyMongo(app)
db = mongo.db

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        user = mongo.db.users.find_one({'username': username})
        if user:
            flash('Користувач з таким ім\'ям вже існує!')
            return redirect(url_for('register'))

        mongo.db.users.insert_one({
            'username': username,
            'password': hashed_password
        })

        flash('Реєстрація пройшла успішно! Тепер можна увійти.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = mongo.db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Невірне ім\'я користувача або пароль!')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    courses = list(mongo.db.courses.find())
    return render_template('dashboard.html', courses=courses)

@app.route('/create_course', methods=['POST'])
def create_course():
    if 'username' not in session:
        return redirect(url_for('login'))

    course_name = request.form['course_name']
    course_description = request.form['course_description']

    mongo.db.courses.insert_one({
        'name': course_name,
        'description': course_description,
        'created_by': session['username'],
        'created_at': datetime.datetime.utcnow()
    })

    return redirect(url_for('dashboard'))

@app.route('/course/<course_id>')
def course(course_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    course = mongo.db.courses.find_one({'_id': ObjectId(course_id)})
    tests = list(mongo.db.tests.find({'course_id': ObjectId(course_id)}))
    courses = list(mongo.db.courses.find())
    return render_template('course.html', course=course, tests=tests, courses=courses)

@app.route('/create_test/<course_id>', methods=['GET', 'POST'])
def create_test(course_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        test_name = request.form.get('test_name')
        questions = request.form.getlist('questions')

        if not test_name or not questions:
            flash('Назва тесту і питання обов\'язкові для заповнення.')
            return redirect(url_for('course', course_id=course_id))

        try:
            mongo.db.tests.insert_one({
                'name': test_name,
                'course_id': ObjectId(course_id),
                'questions': questions,
                'created_by': session['username'],
                'created_at': datetime.datetime.utcnow()
            })

            flash('Тест успішно створений.')
        except Exception as e:
            flash(f'Помилка при створенні тесту: {str(e)}')
            return redirect(url_for('course', course_id=course_id))

    return render_template('create_test.html', course_id=course_id)

@app.route('/edit_test/<test_id>', methods=['GET', 'POST'])
def edit_test(test_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    test = mongo.db.tests.find_one({'_id': ObjectId(test_id)})
    if request.method == 'POST':
        test_name = request.form.get('test_name')
        questions = request.form.getlist('questions')

        if not test_name or not questions:
            flash('Назва тесту і питання обов\'язкові для заповнення.')
            return redirect(url_for('edit_test', test_id=test_id))

        mongo.db.tests.update_one({'_id': ObjectId(test_id)}, {'$set': {'name': test_name, 'questions': questions}})
        flash('Тест успішно оновлений.')
        return redirect(url_for('admin_panel'))

    return render_template('edit_test.html', test=test)

@app.route('/tests')
def tests():
    if 'username' not in session:
        return redirect(url_for('login'))

    all_tests = mongo.db.tests.find()
    return render_template('tests.html', tests=all_tests)

@app.route('/test/<test_id>')
def test(test_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    test = mongo.db.tests.find_one({'_id': ObjectId(test_id)})
    if not test:
        abort(404)
    return render_template('test.html', test=test)

@app.route('/admin')
def admin_panel():
    if 'username' not in session or not session['username'] == '11111':
        return redirect(url_for('login'))
    
    users = list(db.users.find())
    courses = list(db.courses.find())
    tests = list(db.tests.find())
    
    return render_template('admin.html', users=users, courses=courses, tests=tests)

@app.route('/admin/edit_user/<user_id>', methods=['POST'])
def edit_user(user_id):
    username = request.form['username']
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'username': username}})
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    db.users.delete_one({'_id': ObjectId(user_id)})
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit_course/<course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        db.courses.update_one({'_id': ObjectId(course_id)}, {'$set': {'name': name, 'description': description}})
        flash('Курс успішно оновлений.')
        return redirect(url_for('admin_panel'))
    course = db.courses.find_one({'_id': ObjectId(course_id)})
    return render_template('edit_course.html', course=course)

@app.route('/admin/delete_course/<course_id>', methods=['POST'])
def delete_course(course_id):
    db.courses.delete_one({'_id': ObjectId(course_id)})
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_test/<test_id>', methods=['POST'])
def delete_test(test_id):
    db.tests.delete_one({'_id': ObjectId(test_id)})
    return redirect(url_for('admin_panel'))


@app.route('/export_data_json', methods=['GET'])
def export_data_json():
    users = list(db.users.find())
    courses = list(db.courses.find())
    tests = list(db.tests.find())
    
    def convert_objectid_to_str(document):
        """Рекурсивная функция для преобразования всех ObjectId в строки."""
        if isinstance(document, dict):
            for key, value in document.items():
                if isinstance(value, ObjectId):
                    document[key] = str(value)
                elif isinstance(value, (dict, list)):
                    convert_objectid_to_str(value)
        elif isinstance(document, list):
            for index in range(len(document)):
                convert_objectid_to_str(document[index])
    
    for collection in (users, courses, tests):
        convert_objectid_to_str(collection)
    
    data = {
        'users': users,
        'courses': courses,
        'tests': tests
    }
    return jsonify(data)



@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

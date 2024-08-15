from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'ADTProject',
    'port': '8889'
}

# Establish MySQL Connection
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Authentication decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['logged_in'] = True
        session['user_id'] = user['user_id']
        session['user_type'] = user['user_type']
        if user['user_type'] == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('comparison'))
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conf_password = generate_password_hash(request.form['confirm_password'])
        print(password)
        print(conf_password)
        email = request.form['email']
        user_type = request.form['user_type']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, email, user_type) VALUES (%s, %s, %s, %s)',
                           (username, password, email, user_type))
            conn.commit()
        except mysql.connector.Error as err:
            print("Failed to insert data: {}".format(err))
            return redirect(url_for('register'))  # Redirect back to registration on failure
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('user_type', None)
    return redirect(url_for('home'))

@app.route('/comparison', methods=['GET', 'POST'])
@login_required
def comparison():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    base_query = "SELECT * FROM laptops WHERE 1=1"
    query_params = []

    if request.method == 'POST':
        if request.form['brand']:
            base_query += " AND brand LIKE %s ORDER BY brand ASC"
            query_params.append('%' + request.form['brand'] + '%')
        if request.form['model']:
            base_query += " AND model LIKE %s ORDER BY model ASC"
            query_params.append('%' + request.form['model'] + '%')
        if request.form['processor']:
            base_query += " AND processor_brand LIKE %s ORDER BY processor_brand ASC"
            query_params.append('%' + request.form['processor'] + '%')
        if request.form['max_price']:
            base_query += " AND price <= %s ORDER BY price ASC"
            query_params.append(request.form['max_price'])

    cursor.execute(base_query, tuple(query_params))
    laptops = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('comparison.html', laptops=laptops)

@app.route('/compare', methods=['POST'])
def compare():
    selected_ids = request.form.getlist('compare')
    if not selected_ids:
        return redirect(url_for('comparison'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    placeholders = ', '.join(['%s'] * len(selected_ids))
    cursor.execute(f"SELECT * FROM laptops WHERE laptop_id IN ({placeholders})", tuple(selected_ids))
    comparison_laptops = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('compare.html', laptops=comparison_laptops)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM laptops")
    laptops = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin.html', laptops=laptops)

@app.route('/edit/<int:laptop_id>', methods=['GET', 'POST'])
def edit_laptop(laptop_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        # Collecting the form data
        laptop_id = request.form['laptop_id']
        brand = request.form['brand']
        model = request.form['model']
        price = request.form['price']
        rating = request.form['rating']
        processor_brand = request.form['processor_brand']
        processor_tier = request.form['processor_tier']
        num_cores = request.form['num_cores']
        num_threads = request.form['num_threads']
        ram_memory = request.form['ram_memory']
        primary_storage_type = request.form['primary_storage_type']
        primary_storage_capacity = request.form['primary_storage_capacity']
        gpu_brand = request.form['gpu_brand']
        gpu_type = request.form['gpu_type']
        is_touch_screen = request.form['is_touch_screen']
        display_size = request.form['display_size']
        resolution_width = request.form['resolution_width']
        resolution_height = request.form['resolution_height']
        OS=request.form['OS']
        warranty=request.form['warranty']
        # Update query
        cursor.execute("""
            UPDATE laptops SET brand=%s, model=%s, price=%s, rating=%s, processor_brand=%s, processor_tier=%s, num_cores=%s, num_threads=%s, ram_memory=%s, primary_storage_type=%s, primary_storage_capacity=%s, gpu_brand=%s, gpu_type=%s, is_touch_screen=%s, display_size=%s, resolution_width=%s, resolution_height=%s, OS=%s, warranty=%s WHERE laptop_id=%s
            """, (brand, model, price, rating, processor_brand, processor_tier, num_cores, num_threads, ram_memory, primary_storage_type, primary_storage_capacity, gpu_brand, gpu_type, is_touch_screen, display_size, resolution_width, resolution_height, OS, warranty, laptop_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin'))

    # Load existing data for GET request
    cursor.execute("SELECT * FROM laptops WHERE laptop_id = %s", (laptop_id,))
    laptop = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('edit_laptop.html', laptop=laptop)

@app.route('/insert', methods=['GET', 'POST'])
@login_required
def insert_laptop():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':

        # Collecting the form data
        brand = request.form['brand']
        model = request.form['model']
        price = request.form['price']
        rating = request.form['rating']
        processor_brand = request.form['processor_brand']
        processor_tier = request.form['processor_tier']
        num_cores = request.form['num_cores']
        num_threads = request.form['num_threads']
        ram_memory = request.form['ram_memory']
        primary_storage_type = request.form['primary_storage_type']
        primary_storage_capacity = request.form['primary_storage_capacity']
        gpu_brand = request.form['gpu_brand']
        gpu_type = request.form['gpu_type']
        is_touch_screen = request.form['is_touch_screen']
        display_size = request.form['display_size']
        resolution_width = request.form['resolution_width']
        resolution_height = request.form['resolution_height']
        OS = request.form['OS']
        warranty = request.form['warranty']
        # Insert query
        query = """INSERT INTO laptops (brand, model, price, rating, processor_brand, processor_tier, num_cores, num_threads, ram_memory, primary_storage_type, primary_storage_capacity, gpu_brand, gpu_type, is_touch_screen, display_size, resolution_width, resolution_height, OS, warranty) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (brand, model, price, rating, processor_brand, processor_tier, num_cores, num_threads, ram_memory, primary_storage_type, primary_storage_capacity, gpu_brand, gpu_type, is_touch_screen, display_size, resolution_width, resolution_height, OS, warranty)       
        cursor.execute("""INSERT INTO laptops (brand, model, price, rating, processor_brand, processor_tier, num_cores, num_threads, ram_memory, primary_storage_type, primary_storage_capacity, gpu_brand, gpu_type, is_touch_screen, display_size, resolution_width, resolution_height, OS, warranty) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", values)
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('admin'))

    return render_template('insert_laptop.html')

@app.route('/delete/<int:laptop_id>', methods=['POST','GET'])
@login_required
def delete_laptop(laptop_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM laptops WHERE laptop_id = %s", (laptop_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0',port='8000')

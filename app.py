from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            supplier TEXT,
            expiration_date TEXT
        );
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT
        );
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        supplier = request.form['supplier']
        expiration_date = request.form['expiration_date']
        conn = get_db_connection()
        conn.execute('INSERT INTO products (name, quantity, supplier, expiration_date) VALUES (?, ?, ?, ?)',
                     (name, quantity, supplier, expiration_date))
        conn.commit()
        conn.close()
        flash('✅ تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('index'))
    return render_template('add_product.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        supplier = request.form['supplier']
        expiration_date = request.form['expiration_date']
        conn.execute('UPDATE products SET name = ?, quantity = ?, supplier = ?, expiration_date = ? WHERE id = ?',
                     (name, quantity, supplier, expiration_date, id))
        conn.commit()
        conn.close()
        flash('✏️ تم تعديل المنتج بنجاح', 'info')
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/delete/<int:id>')
def delete_product(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('🗑️ تم حذف المنتج', 'warning')
    return redirect(url_for('index'))

# -------- الموردين --------

@app.route('/suppliers')
def suppliers():
    conn = get_db_connection()
    all_suppliers = conn.execute('SELECT * FROM suppliers').fetchall()
    conn.close()
    return render_template('suppliers.html', suppliers=all_suppliers)

@app.route('/add_supplier', methods=['GET', 'POST'])
def add_supplier():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        conn = get_db_connection()
        conn.execute('INSERT INTO suppliers (name, phone, email) VALUES (?, ?, ?)', (name, phone, email))
        conn.commit()
        conn.close()
        flash("✅ تم إضافة المورد بنجاح", 'success')
        return redirect(url_for('suppliers'))
    return render_template('add_supplier.html')

@app.route('/delete_supplier/<int:id>')
def delete_supplier(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM suppliers WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash("🗑️ تم حذف المورد", 'info')
    return redirect(url_for('suppliers'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

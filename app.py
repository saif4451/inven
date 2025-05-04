from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    
    # إنشاء جدول المنتجات
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            supplier TEXT,
            expiration_date TEXT
        )
    ''')
    
    # إنشاء جدول المبيعات اليومية
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            total_sales REAL NOT NULL,
            total_items INTEGER NOT NULL,
            total_customers INTEGER NOT NULL,
            details TEXT
        )
    ''')
    
    # إنشاء جدول الفواتير
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT NOT NULL,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            total_price REAL,
            customer_id INTEGER,
            customer_name TEXT
        )
    ''')
    
    # إنشاء جدول الحسابات
    c.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    conn.commit()
    conn.close()

def add_sample_data():
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    
    # إضافة بيانات تجريبية
    sample_data = [
        ('2024-05-01', 1500.0, 5, 'شيبسي: 3 قطع - 300 جنيه\nبسكوت: 2 قطع - 1200 جنيه'),
        ('2024-05-02', 2000.0, 8, 'شيبسي: 5 قطع - 500 جنيه\nبسكوت: 3 قطع - 1500 جنيه'),
        ('2024-05-03', 1800.0, 6, 'شيبسي: 4 قطع - 400 جنيه\nبسكوت: 2 قطع - 1400 جنيه')
    ]
    
    c.executemany('''
        INSERT INTO daily_sales (date, total_sales, total_items, details)
        VALUES (?, ?, ?, ?)
    ''', sample_data)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
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
        
        flash('تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('index'))
    return render_template('add_product.html')

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
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
        
        flash('تم تعديل المنتج بنجاح', 'success')
        return redirect(url_for('index'))
    
    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('تم حذف المنتج بنجاح', 'success')
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

@app.route('/history')
def history():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    
    # جلب المبيعات للتاريخ المحدد
    c.execute('''
        SELECT * FROM daily_sales 
        WHERE date = ? 
        ORDER BY date DESC
    ''', (date,))
    
    sales = c.fetchall()
    
    # جلب مبيعات اليوم
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''
        SELECT 
            COALESCE(SUM(total_price), 0) as total_sales,
            COALESCE(COUNT(DISTINCT product_id), 0) as total_items,
            COALESCE(COUNT(DISTINCT customer_id), 0) as total_customers
        FROM invoices 
        WHERE sale_date = ?
    ''', (today,))
    
    today_sales = c.fetchone()
    
    # إذا لم تكن هناك مبيعات، نضيف بيانات تجريبية
    if not sales:
        # إضافة بيانات تجريبية للمبيعات
        sample_data = [
            ('2024-05-01', 1500.0, 5, 3, 'شيبسي: 3 قطع - 300 جنيه - العميل: أحمد\nبسكوت: 2 قطع - 1200 جنيه - العميل: محمد'),
            ('2024-05-02', 2000.0, 8, 4, 'شيبسي: 5 قطع - 500 جنيه - العميل: علي\nبسكوت: 3 قطع - 1500 جنيه - العميل: خالد'),
            ('2024-05-03', 1800.0, 6, 3, 'شيبسي: 4 قطع - 400 جنيه - العميل: سعيد\nبسكوت: 2 قطع - 1400 جنيه - العميل: محمود')
        ]
        
        c.executemany('''
            INSERT INTO daily_sales (date, total_sales, total_items, total_customers, details)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_data)
        
        conn.commit()
        
        # جلب المبيعات مرة أخرى بعد إضافة البيانات التجريبية
        c.execute('''
            SELECT * FROM daily_sales 
            WHERE date = ? 
            ORDER BY date DESC
        ''', (date,))
        
        sales = c.fetchall()
    
    conn.close()
    
    return render_template('history.html', 
                         sales=sales, 
                         selected_date=date,
                         today_sales=today_sales)

@app.route('/sale_details/<int:sale_id>')
def sale_details(sale_id):
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    
    c.execute('SELECT details FROM daily_sales WHERE id = ?', (sale_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return jsonify({'details': result[0]})
    else:
        return jsonify({'details': 'لا توجد تفاصيل متاحة'})

@app.route('/accounts')
def accounts():
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    
    # جلب جميع الحسابات
    c.execute('SELECT * FROM accounts ORDER BY date DESC')
    accounts = c.fetchall()
    
    # حساب إجمالي الديون والمدفوعات
    c.execute('SELECT SUM(amount) FROM accounts WHERE type = "debt" AND status = "pending"')
    total_debt = c.fetchone()[0] or 0
    
    c.execute('SELECT SUM(amount) FROM accounts WHERE type = "payment"')
    total_payments = c.fetchone()[0] or 0
    
    conn.close()
    
    return render_template('accounts.html', 
                         accounts=accounts,
                         total_debt=total_debt,
                         total_payments=total_payments)

@app.route('/add_account', methods=['POST'])
def add_account():
    customer_name = request.form['customer_name']
    amount = float(request.form['amount'])
    account_type = request.form['type']
    description = request.form.get('description', '')
    
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO accounts (customer_name, amount, date, type, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (customer_name, amount, datetime.now().strftime('%Y-%m-%d'), account_type, description))
    
    conn.commit()
    conn.close()
    
    flash('تم إضافة الحساب بنجاح', 'success')
    return redirect(url_for('accounts'))

@app.route('/mark_paid/<int:account_id>')
def mark_paid(account_id):
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    
    c.execute('UPDATE accounts SET status = "paid" WHERE id = ?', (account_id,))
    
    conn.commit()
    conn.close()
    
    flash('تم تحديث حالة الحساب', 'success')
    return redirect(url_for('accounts'))

@app.route('/save_today_sales', methods=['POST'])
def save_today_sales():
    try:
        conn = sqlite3.connect('supermarket.db')
        c = conn.cursor()
        
        # جلب مبيعات اليوم من جدول الفواتير
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''
            SELECT 
                COALESCE(SUM(total_price), 0) as total_sales,
                COALESCE(COUNT(DISTINCT product_id), 0) as total_items,
                COALESCE(COUNT(DISTINCT customer_id), 0) as total_customers,
                GROUP_CONCAT(
                    product_name || ': ' || 
                    quantity || ' قطعة - ' || 
                    total_price || ' جنيه - ' ||
                    'العميل: ' || customer_name, '\n'
                ) as details
            FROM invoices 
            WHERE sale_date = ?
        ''', (today,))
        
        result = c.fetchone()
        
        # إذا لم تكن هناك مبيعات، نضيف بيانات تجريبية
        if result['total_sales'] == 0:
            # إضافة بيانات تجريبية للفواتير
            sample_invoices = [
                (today, 1, 'شيبسي', 3, 300, 1, 'أحمد'),
                (today, 2, 'بسكوت', 2, 1200, 2, 'محمد')
            ]
            
            c.executemany('''
                INSERT INTO invoices (sale_date, product_id, product_name, quantity, total_price, customer_id, customer_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', sample_invoices)
            
            conn.commit()
            
            # جلب البيانات مرة أخرى
            c.execute('''
                SELECT 
                    COALESCE(SUM(total_price), 0) as total_sales,
                    COALESCE(COUNT(DISTINCT product_id), 0) as total_items,
                    COALESCE(COUNT(DISTINCT customer_id), 0) as total_customers,
                    GROUP_CONCAT(
                        product_name || ': ' || 
                        quantity || ' قطعة - ' || 
                        total_price || ' جنيه - ' ||
                        'العميل: ' || customer_name, '\n'
                    ) as details
                FROM invoices 
                WHERE sale_date = ?
            ''', (today,))
            
            result = c.fetchone()
        
        # حفظ في جدول daily_sales
        c.execute('''
            INSERT INTO daily_sales (date, total_sales, total_items, total_customers, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (today, result['total_sales'], result['total_items'], result['total_customers'], result['details']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'تم حفظ المبيعات بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# استدعاء الدوال عند بدء التطبيق
init_db()
add_sample_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

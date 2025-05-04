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
    
    # حذف وإعادة إنشاء جدول المنتجات
    c.execute('DROP TABLE IF EXISTS products')
    c.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            supplier TEXT,
            expiration_date TEXT,
            received_date TEXT NOT NULL
        )
    ''')
    
    # حذف وإعادة إنشاء جدول الفواتير
    c.execute('DROP TABLE IF EXISTS invoices')
    c.execute('''
        CREATE TABLE invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            sale_date TEXT NOT NULL,
            total_amount REAL NOT NULL,
            customer_name TEXT,
            notes TEXT
        )
    ''')
    
    # حذف وإعادة إنشاء جدول تفاصيل الفواتير
    c.execute('DROP TABLE IF EXISTS invoice_items')
    c.execute('''
        CREATE TABLE invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
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
    
    # إنشاء جدول العملاء
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT
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
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    
    # جلب المنتجات الواردة حديثاً (خلال آخر 7 أيام)
    c.execute('''
        SELECT * FROM products 
        WHERE date(received_date) >= date('now', '-7 days')
        ORDER BY received_date DESC
    ''')
    products = [dict(zip([column[0] for column in c.description], row)) for row in c.fetchall()]
    
    conn.close()
    return render_template('index.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            conn = sqlite3.connect('supermarket.db')
            c = conn.cursor()
            
            name = request.form['name']
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            supplier = request.form.get('supplier', '')
            expiration_date = request.form.get('expiration_date', '')
            received_date = datetime.now().strftime('%Y-%m-%d')
            
            c.execute('''
                INSERT INTO products (name, price, quantity, supplier, expiration_date, received_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, price, quantity, supplier, expiration_date, received_date))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'تم إضافة المنتج بنجاح'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    return render_template('add_product.html')

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()

    if request.method == 'POST':
        try:
            name = request.form['name']
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            supplier = request.form.get('supplier', '')
            expiration_date = request.form.get('expiration_date', '')
            
            c.execute('''
                UPDATE products 
                SET name = ?, price = ?, quantity = ?, supplier = ?, expiration_date = ?
                WHERE id = ?
            ''', (name, price, quantity, supplier, expiration_date, id))
            
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'تم تعديل المنتج بنجاح'})
        except Exception as e:
            conn.close()
            return jsonify({'success': False, 'message': str(e)})
    
    # GET request - عرض نموذج التعديل
    c.execute('SELECT * FROM products WHERE id = ?', (id,))
    product = c.fetchone()
    conn.close()
    
    if product:
        product = dict(zip(['id', 'name', 'price', 'quantity', 'supplier', 'expiration_date'], product))
        return render_template('edit_product.html', product=product)
    else:
        return jsonify({'success': False, 'message': 'المنتج غير موجود'})

@app.route('/delete_product/<int:id>', methods=['DELETE'])
def delete_product(id):
    try:
        conn = sqlite3.connect('supermarket.db')
        c = conn.cursor()
        c.execute('DELETE FROM products WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'تم حذف المنتج بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

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
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    
    # جلب تواريخ المبيعات
    c.execute('''
        SELECT DISTINCT date(sale_date) as sale_date
        FROM invoices
        ORDER BY sale_date DESC
    ''')
    dates = [row[0] for row in c.fetchall()]
    
    # جلب مبيعات اليوم
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''
        SELECT 
            i.invoice_number,
            i.sale_date,
            i.total_amount,
            i.customer_name,
            GROUP_CONCAT(p.name || ' (' || ii.quantity || ' قطعة - ' || ii.total_price || ' جنيه)', '\n') as items
        FROM invoices i
        JOIN invoice_items ii ON i.id = ii.invoice_id
        JOIN products p ON ii.product_id = p.id
        WHERE date(i.sale_date) = ?
        GROUP BY i.id
        ORDER BY i.sale_date DESC
    ''', (today,))
    today_sales = c.fetchall()
    
    conn.close()
    return render_template('history.html', dates=dates, today_sales=today_sales)

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
                GROUP_CONCAT(
                    product_name || ': ' || 
                    quantity || ' قطعة - ' || 
                    total_price || ' جنيه', '\n'
                ) as details
            FROM invoices 
            WHERE sale_date = ?
        ''', (today,))
        
        result = c.fetchone()
        
        # إذا لم تكن هناك مبيعات، نضيف بيانات تجريبية
        if result['total_sales'] == 0:
            # إضافة بيانات تجريبية للفواتير
            sample_invoices = [
                (today, 1, 'شيبسي', 3, 300),
                (today, 2, 'بسكوت', 2, 1200)
            ]
            
            c.executemany('''
                INSERT INTO invoices (sale_date, product_id, product_name, quantity, total_price)
                VALUES (?, ?, ?, ?, ?)
            ''', sample_invoices)
            
            conn.commit()
            
            # جلب البيانات مرة أخرى
            c.execute('''
                SELECT 
                    COALESCE(SUM(total_price), 0) as total_sales,
                    COALESCE(COUNT(DISTINCT product_id), 0) as total_items,
                    GROUP_CONCAT(
                        product_name || ': ' || 
                        quantity || ' قطعة - ' || 
                        total_price || ' جنيه', '\n'
                    ) as details
                FROM invoices 
                WHERE sale_date = ?
            ''', (today,))
            
            result = c.fetchone()
        
        # حفظ في جدول daily_sales
        c.execute('''
            INSERT INTO daily_sales (date, total_sales, total_items, details)
            VALUES (?, ?, ?, ?)
        ''', (today, result['total_sales'], result['total_items'], result['details']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'تم حفظ المبيعات بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/add_sale', methods=['GET', 'POST'])
def add_sale():
    if request.method == 'POST':
        try:
            conn = sqlite3.connect('supermarket.db')
            c = conn.cursor()
            
            # إنشاء رقم فاتورة جديد
            c.execute('SELECT MAX(invoice_number) FROM invoices')
            last_invoice = c.fetchone()[0]
            new_invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{int(last_invoice.split('-')[-1]) + 1 if last_invoice else 1}"
            
            # إضافة الفاتورة
            customer_name = request.form.get('customer_name', '')
            notes = request.form.get('notes', '')
            sale_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            c.execute('''
                INSERT INTO invoices (invoice_number, sale_date, total_amount, customer_name, notes)
                VALUES (?, ?, 0, ?, ?)
            ''', (new_invoice_number, sale_date, customer_name, notes))
            
            invoice_id = c.lastrowid
            
            # إضافة المنتجات المباعة
            total_amount = 0
            products = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            
            for product_id, quantity in zip(products, quantities):
                if not product_id or not quantity:
                    continue
                    
                quantity = int(quantity)
                if quantity <= 0:
                    continue
                
                # جلب معلومات المنتج
                c.execute('SELECT price, quantity FROM products WHERE id = ?', (product_id,))
                product = c.fetchone()
                
                if not product or product[1] < quantity:
                    raise Exception('الكمية غير متوفرة')
                
                price = product[0]
                total_price = price * quantity
                
                # إضافة المنتج للفاتورة
                c.execute('''
                    INSERT INTO invoice_items (invoice_id, product_id, quantity, price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                ''', (invoice_id, product_id, quantity, price, total_price))
                
                # تحديث كمية المنتج
                c.execute('''
                    UPDATE products 
                    SET quantity = quantity - ? 
                    WHERE id = ?
                ''', (quantity, product_id))
                
                total_amount += total_price
            
            # تحديث إجمالي الفاتورة
            c.execute('''
                UPDATE invoices 
                SET total_amount = ? 
                WHERE id = ?
            ''', (total_amount, invoice_id))
            
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'تم إضافة المبيعات بنجاح', 'invoice_number': new_invoice_number})
        except Exception as e:
            conn.rollback()
            conn.close()
            return jsonify({'success': False, 'message': str(e)})
    
    # عرض صفحة إضافة المبيعات
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    c.execute('SELECT id, name, price, quantity FROM products WHERE quantity > 0')
    products = c.fetchall()
    conn.close()
    
    return render_template('add_sale.html', products=products)

@app.route('/products')
def products():
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    c.execute('SELECT * FROM products ORDER BY name')
    products = [dict(zip(['id', 'name', 'price', 'quantity', 'supplier', 'expiration_date'], row)) for row in c.fetchall()]
    conn.close()
    return render_template('products.html', products=products)

@app.route('/customers')
def customers():
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    c.execute('SELECT * FROM customers ORDER BY name')
    customers = c.fetchall()
    conn.close()
    return render_template('customers.html', customers=customers)

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        try:
            conn = sqlite3.connect('supermarket.db')
            c = conn.cursor()
            
            name = request.form['name']
            phone = request.form.get('phone', '')
            address = request.form.get('address', '')
            
            c.execute('''
                INSERT INTO customers (name, phone, address)
                VALUES (?, ?, ?)
            ''', (name, phone, address))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'تم إضافة العميل بنجاح'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    
    return render_template('add_customer.html')

@app.route('/reports')
def reports():
    conn = sqlite3.connect('supermarket.db')
    c = conn.cursor()
    
    # إحصائيات عامة
    c.execute('SELECT COUNT(*), SUM(quantity), SUM(price * quantity) FROM products')
    total_products, total_quantity, total_value = c.fetchone()
    
    # معالجة القيم الفارغة
    total_products = total_products or 0
    total_quantity = total_quantity or 0
    total_value = total_value or 0.0
    
    # المنتجات قليلة الكمية
    c.execute('SELECT * FROM products WHERE quantity < 10')
    low_stock = [dict(zip([column[0] for column in c.description], row)) for row in c.fetchall()]
    
    # المنتجات التي على وشك الانتهاء
    c.execute('''
        SELECT * FROM products 
        WHERE expiration_date != '' 
        AND date(expiration_date) <= date('now', '+30 days')
    ''')
    expiring_soon = [dict(zip([column[0] for column in c.description], row)) for row in c.fetchall()]
    
    # أفضل المنتجات مبيعاً
    c.execute('''
        SELECT p.name, COUNT(*) as total_sold, SUM(p.price) as total_revenue
        FROM invoices i
        JOIN products p ON i.product_id = p.id
        GROUP BY p.id
        ORDER BY total_sold DESC
        LIMIT 5
    ''')
    top_selling = c.fetchall()
    
    # المنتجات المضافة حديثاً
    c.execute('''
        SELECT name, supplier, quantity, received_date
        FROM products
        ORDER BY received_date DESC
        LIMIT 10
    ''')
    recent_products = [dict(zip([column[0] for column in c.description], row)) for row in c.fetchall()]
    
    conn.close()
    
    return render_template('reports.html',
                         products_stats={
                             'total_products': total_products,
                             'total_quantity': total_quantity,
                             'total_value': total_value
                         },
                         low_stock=low_stock,
                         expiring_soon=expiring_soon,
                         top_selling=top_selling,
                         recent_products=recent_products)

# استدعاء الدوال عند بدء التطبيق
init_db()
add_sample_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

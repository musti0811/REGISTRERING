from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import bcrypt
from config import Config
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'hemmeligkey'

mysql = MySQL(app)

# Function to create necessary tables
def create_tables():
    with app.app_context():
        cur = mysql.connection.cursor()
        
        # Create brugere table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS brugere (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            brugernavn VARCHAR(50) NOT NULL UNIQUE,
            navn VARCHAR(100),
            firma VARCHAR(100),
            adgangskode VARCHAR(255) NOT NULL,
            oprettet_dato TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create arbejdstid table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS arbejdstid (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bruger_id INT NOT NULL,
            start_tid DATETIME NOT NULL,
            slut_tid DATETIME,
            total_arbejdstid TIME,
            ip_adresse VARCHAR(45),
            FOREIGN KEY (bruger_id) REFERENCES brugere(id)
        )
        """)
        
        mysql.connection.commit()
        cur.close()

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM brugere WHERE email = %s", [email])
        user = cur.fetchone()
        cur.close()
        
        if user and bcrypt.checkpw(password, user['adgangskode'].encode('utf-8')):
            session['user_id'] = user['id']
            session['email'] = user['email']
            session['username'] = user['brugernavn']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('start_arbejde'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        name = request.form['name']
        company = request.form['company']
        password = request.form['password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO brugere (email, brugernavn, navn, firma, adgangskode)
                VALUES (%s, %s, %s, %s, %s)
            """, (email, username, name, company, hashed_password.decode('utf-8')))
            mysql.connection.commit()
            flash('User registered successfully!', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error occurred during registration: {str(e)}', 'danger')
        finally:
            cur.close()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/start_arbejde')
def start_arbejde():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'danger')
        return redirect(url_for('login'))
    
    ip_adresse = request.remote_addr
    return render_template('start_arbejde.html', ip_adresse=ip_adresse)

@app.route('/start_timer', methods=['POST'])
def start_timer():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'danger')
        return redirect(url_for('login'))
    
    start_tid = datetime.now()
    bruger_id = session['user_id']
    ip_adresse = request.form['ip_adresse']
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO arbejdstid (bruger_id, start_tid, ip_adresse)
        VALUES (%s, %s, %s)
    """, (bruger_id, start_tid, ip_adresse))
    mysql.connection.commit()
    cur.close()
    
    flash('Work started!', 'success')
    return redirect(url_for('slut_arbejde'))

@app.route('/slut_arbejde', methods=['GET', 'POST'])
def slut_arbejde():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        slut_tid = datetime.now()
        bruger_id = session['user_id']
        ip_adresse = request.remote_addr

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT start_tid FROM arbejdstid
            WHERE bruger_id = %s AND slut_tid IS NULL
        """, [bruger_id])
        start_tid = cur.fetchone()['start_tid']
        
        if start_tid:
            total_arbejdstid = slut_tid - start_tid

            cur.execute("""
                UPDATE arbejdstid
                SET slut_tid = %s, total_arbejdstid = %s
                WHERE bruger_id = %s AND slut_tid IS NULL
            """, (slut_tid, total_arbejdstid, bruger_id))
            mysql.connection.commit()
            cur.close()

            flash('Work ended!', 'success')
            return redirect(url_for('login'))
        else:
            flash('No ongoing work session found!', 'danger')
            return redirect(url_for('start_arbejde'))
    
    return render_template('slut_arbejde.html')

if __name__ == '__main__':
    # Create tables if they don't exist
    create_tables()
    app.run(debug=True)

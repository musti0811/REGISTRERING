from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import bcrypt
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'hemmeligkey'

mysql = MySQL(app)    


@app.route('/test_db')
def test_db():
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT 1")
            result = cur.fetchone()
            cur.close()
            if result:
                return "Databaseforbindelse er OK!"
            else:
                return "Ingen resultater fra databasen."
        except Exception as e:
            return f"Fejl ved forbindelse til databasen: {e}"
    
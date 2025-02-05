from flask import Flask, request, render_template
import mysql.connector
from mysql.connector import Error
import re
import html

app = Flask(__name__, template_folder='templates')

db_config = {
   'host': 'localhost', 
   'user': 'root',
   'password': 'Jackychan@123',
   'database': 'password_system'
}

def sanitize_input(input_string):
   cleaned = re.sub(r'[;\'\"\\]', '', input_string)
   return html.escape(cleaned)

def get_db_connection():
   try:
       return mysql.connector.connect(**db_config)
   except Error as e:
       print(f"Error connecting to database: {e}")
       return None

@app.route('/')
@app.route('/app2')
@app.route('/app2/')
def home():
    return render_template('login.html')
@app.route('/app2/action2', methods=['POST'])
def validate_password():
   conn = None
   cursor = None
   try:
       password = sanitize_input(request.form.get('password', ''))
       
       if not password or len(password) > 100:
           return "Invalid input length", 400
           
       conn = get_db_connection()
       if not conn:
           return "Database connection error", 500

       query = "SELECT EXISTS(SELECT 1 FROM passwords WHERE password_hash = %s) as valid"
               
       cursor = conn.cursor(dictionary=True, prepared=True)
       cursor.execute(query, (password,))
       result = cursor.fetchone()

       return "Authenticated!" if result and result['valid'] == 1 else "Invalid Password!"

   except Error as e:
       print(f"Database error: {e}")
       return "Database error occurred", 500
       
   except Exception as e:
       print(f"Unexpected error: {e}")
       return "An error occurred", 500
       
   finally:
       if cursor: cursor.close()
       if conn: conn.close()

if __name__ == '__main__':
   app.run(host='0.0.0.0', debug=True)
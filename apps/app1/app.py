from flask import Flask, request, render_template
import mysql.connector

app = Flask(__name__, template_folder='templates')

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Jackychan@123',
    'database': 'password_system'
}

@app.route('/')
@app.route('/app1')
@app.route('/app1/')
def home():
    return render_template('login.html')

@app.route('/app1/action1', methods=['POST'])
def validate_password():
    password = request.form.get('password')
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT EXISTS(SELECT 1 FROM passwords WHERE password_hash = '{password}') as valid"
        cursor.execute(query)
        result = cursor.fetchone()
        
        return "Authenticated!" if result['valid'] == 1 else "Invalid Password!"
            
    except Exception as e:
        return f"Error: {str(e)}"
        
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
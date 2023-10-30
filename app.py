from flask import Flask, request, jsonify
import mysql.connector
import datetime
from flask_cors import CORS 

app = Flask(__name__)

# Configure MySQL database connection
db_connection = mysql.connector.connect(
    host='database-1.cqmz08yhaga0.us-east-2.rds.amazonaws.com',
    user='admin_syllabuddy',
    password='zozRun-sopgu0-gysrip',
    database='syllabuddy'
)

# Enable CORS for the entire app
CORS(app)

# TODO: fill this out
@app.route('/login', methods=['GET'])
def login_user():
    pass

# Endpoint for user registration
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()

    # Check if the request data is received correctly
    if not data:
        return jsonify({'error': 'Invalid request data'})

    cursor = db_connection.cursor()

    try:
        # Check if email or phone number already exist
        check_query = """
        SELECT COUNT(*) FROM Users
        WHERE email = %s OR phoneNumber = %s
        """
        cursor.execute(check_query, (data.get('email', ''), data.get('phoneNumber', '')))
        result = cursor.fetchone()

        if result and result[0] > 0:
            # User with the same email or phone number already exists
            cursor.close()
            return jsonify({'error': 'An account already exists with this information. Please log in.'})

        # If no existing user is found, proceed with registration
        registration_date = datetime.datetime.now()
        insert_query = """
        INSERT INTO Users (username, password, userType, lastName, firstName, email, phoneNumber, registrationDate)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            data.get('username', ''), data.get('password', ''), data.get('userType', ''),
            data.get('lastName', ''), data.get('firstName', ''), data.get('email', ''),
            data.get('phoneNumber', ''), registration_date
        ))
        db_connection.commit()
        cursor.close()
        return jsonify({'message': 'User registered successfully'})
    except Exception as e:
        return jsonify({'error': 'An error occurred while registering the user.'})

if __name__ == '__main__':
    app.run()

from flask import Flask, request, jsonify, url_for
import mysql.connector
import datetime

app = Flask(__name__)

# Configure MySQL database connection
db_connection = mysql.connector.connect(
    host='database-1.cqmz08yhaga0.us-east-2.rds.amazonaws.com',
    user='admin_syllabuddy',  
    password='zozRun-sopgu0-gysrip', 
    database='syllabuddy'
)

# TODO: fill this out
@app.route('/login', methods=['GET'])
def login_user():
    pass

# Endpoint for user registration
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    cursor = db_connection.cursor()

    # Check if email or phone number already exist
    check_query = """
    SELECT COUNT(*) FROM Users
    WHERE email = %s OR phoneNumber = %s
    """
    
    cursor.execute(check_query, (data['email'], data['phoneNumber']))
    result = cursor.fetchone()
    if result and result[0] > 0:
        # User with the same email or phone number already exists
        cursor.close()
        return jsonify({'error': 'An account already exists with this information. Please log in.'})

    # If no existing user is found, proceed with registration
    try:
        registration_date = datetime.datetime.now()
        insert_query = """
        INSERT INTO Users (username, password, userType, lastName, firstName, email, phoneNumber, registrationDate)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            data['username'], data['password'], data['userType'], 
            data['lastName'], data['firstName'], data['email'], 
            data['phoneNumber'], registration_date
        ))
        db_connection.commit()
        cursor.close()
        return jsonify({'message': 'User registered successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})
    
if __name__ == '__main__':
    app.run()

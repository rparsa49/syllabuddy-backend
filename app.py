from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# Configure MySQL database connection
db_connection = mysql.connector.connect(
    host='167.206.126.218',
    user='syllabuddy-user',  
    password='password', 
    database='your_database'  # Replace with the name of your MySQL database
)

# Endpoint for user registration (FIX DB/TABLE NAMES LATER)
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    cursor = db_connection.cursor()

    # Define the SQL query to insert user data
    insert_query = "INSERT INTO Users (email, password, role, university) VALUES (%s, %s, %s, %s)"

    try:
        # Execute the SQL query with user data
        cursor.execute(insert_query, (data['email'], data['password'], data['role'], data['university']))
        db_connection.commit()  
        cursor.close()
        return jsonify({'message': 'User registered successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()

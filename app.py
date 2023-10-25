from flask import Flask, request, jsonify
import pyodbc

app = Flask(__name__)

# Configure your database connection (ADD ACTUAL DATABASE INFO LATER)
db_connection = pyodbc.connect(
    "Driver={SQL Server};"
    "Server=your_server;"
    "Database=your_database;"
    "UID=your_username;"
    "PWD=your_password;"
)

# Endpoint for user registration (FIX TABLE NAMES LATER)
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    cursor = db_connection.cursor()
    
    # Define the SQL query to insert user data
    insert_query = "INSERT INTO Users (email, password, role, university) VALUES (?, ?, ?, ?)"
    
    try:
        # Execute the SQL query with user data
        cursor.execute(insert_query, (data['email'], data['password'], data['role'], data['university']))
        db_connection.commit()  # Commit the changes to the database
        cursor.close()
        return jsonify({'message': 'User registered successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()

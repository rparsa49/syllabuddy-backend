from flask import Flask, request, jsonify
import mysql.connector
import datetime
import json
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequest, Unauthorized, Conflict

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

app.secret_key = "lF!}'dcq4*,BaTH"

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    user = User(user_id)
    return user


# Endpoint for user login
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        if not data:
            raise BadRequest('Invalid request data')

        cursor = db_connection.cursor()

        try:
            # Check if a user with the provided email exists
            check_query = """
            SELECT userId, password FROM Users
            WHERE email = %s
            """
            cursor.execute(check_query, (data.get('email', ''),))
            result = cursor.fetchone()

            if result:
                user_id, hashed_password = result

                # Check if the provided password matches the hashed password in the database
                if check_password_hash(hashed_password, data.get('password', '')):
                    # Log in the user after successful login
                    user = User(user_id)
                    login_user(user)
                    return jsonify({'user_id': user_id, 'message': 'User successfully logged in'})

            cursor.close()
            raise Unauthorized('Incorrect email or password')

        except Exception as e:
            raise BadRequest('An error occurred while logging in: ' + str(e))

    except BadRequest:
        raise BadRequest('Invalid request data')


# Endpoint for user registration
@app.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        print(request.method)
        # Check if the request data is received correctly
        if not data:
            raise BadRequest('Invalid request data')

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
                raise Conflict('An account already exists with this information. Please log in.')

            # Hash the password before storing it
            hashed_password = generate_password_hash(data.get('password', ''))

            # If no existing user is found, proceed with registration
            registration_date = datetime.datetime.now()
            insert_query = """
            INSERT INTO Users (username, password, userType, lastName, firstName, email, phoneNumber, registrationDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                data.get('userName', ''), hashed_password, data.get('userType', ''),
                data.get('lastName', ''), data.get('firstName', ''), data.get('email', ''),
                data.get('phoneNumber', ''), registration_date
            ))
            db_connection.commit()
            cursor.close()

            # Log in the user after successful registration
            user = User(cursor.lastrowid)
            login_user(user)

            return jsonify({'message': 'User registered successfully'})
        except Exception as e:
            raise BadRequest('An error occurred while registering the user: ' + str(e))
    except BadRequest:
        raise BadRequest('Invalid request data')

# Endpoint for user to add course
@app.route('/addcourse', methods=['POST'] )
def add_course():
    try:
        data = request.get_json()
        print(request.method)
        # Check if the request data is received correctly
        if not data:
            raise BadRequest('Invalid request data')

        cursor = db_connection.cursor()
        try:

            #Get Syllabus contents
            syllabus = data.get('syllabus')
            contents = syllabus.read()

            #Get UniversityID
            check_query = """
            SELECT universityID FROM Universities WHERE universityName = %s
            """

            cursor.execute(check_query, (data.get('selectedUniversity', ''),))
            result = cursor.fetchall()
            if result:
                universityID = result[0][0]

            #Get ProfessorID
            check_query = """
            SELECT professorID FROM Professor WHERE firstname = %s AND lastname = %s
            """

            cursor.execute(check_query, (data.get('profFirstname', ''), data.get('profLastname', '')))
            result = cursor.fetchall()
            if result:
                professorID = result[0][0]
            else:
                insert_query = """
                INSERT INTO Professor (professorID, universityID, firstname, lastname)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    None,
                    universityID,
                    data.get('profFirstname', ''),
                    data.get('profLastname', '')
                ))
                db_connection.commit()
                
                

                check_query = """
                SELECT professorID FROM Professor WHERE firstname = %s AND lastname = %s
                """

                cursor.execute(check_query, (data.get('profFirstname', ''), data.get('profLastname', '')))
                result = cursor.fetchall()
                professorID = result[0][0]
                
            
            # Check if course code AT THAT UNIVERSITY already exists
            check_query = """
            SELECT COUNT(*)
            FROM course
            WHERE courseCode = %s AND universityID = %s
            """
            cursor.execute(check_query, (data.get('courseCode', ''), universityID))
            result = cursor.fetchone()

            # If no existing course is found, proceed with adding it.
            insert_query = """
            INSERT INTO course (courseID, courseCode, courseName, professorID, universityID, courseDescription, averageGrade, tags, term, syllabus)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, ( 
                data.get('courseCode', ''), 
                data.get('courseName', ''),
                professorID, 
                universityID, 
                data.get('courseDesc', ''),
                data.get('averageGrade', ''),
                data.get('jsonTagsData', ''),
                data.get('term', ''),
                contents
            ))

            db_connection.commit()
            cursor.close()

            if result and result[0] > 0:
                # course code already exists at this university
                cursor.close()
                raise Conflict('A course already exists with this course code at this university.  Please adjust your input.')

        except Exception as e:
            raise BadRequest('An error occurred while adding the course: ' + str(e))
    except BadRequest:
        raise BadRequest('Invalid request data')

# Endpoint to logout user and end their session
@app.route('/logout', methods=['POST'])
def logout_user():
    if current_user.is_authenticated:
        # Log out the current user
        logout_user()
        return jsonify({'message': 'User successfully logged out'})
    else:
        return jsonify({'message': 'No user is currently logged in'})


if __name__ == '__main__':
    app.run()
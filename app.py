from flask import Flask, request, jsonify 
import mysql.connector
import datetime
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
    def __init__(self, user_id, user_name):
        self.id = user_id
        self.name = user_name

@login_manager.user_loader
def load_user(user_id, user_name):
    user = User(user_id)
    name = User(user_name)
    return user, name


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
                    name_query = """
                    SELECT firstName FROM Users
                    WHERE email = %s
                    """
                    cursor.execute(name_query, (data.get('email', ''),))
                    name = cursor.fetchone()
                    name = name[0]
                    # Log in the user after successful login
                    user = User(user_id, name)
                    login_user(user)
                    return jsonify({'user_id': user_id, 'user_name': name, 'message': 'User successfully logged in'})

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

            # Get UniversityID
            check_query = """
            SELECT universityID FROM Universities WHERE universityName = %s
            """
            cursor.execute(check_query, (data.get('University', ''),))
            result = cursor.fetchall()
            if result:
                universityID = result[0][0]
            
            # If no existing user is found, proceed with registration
            registration_date = datetime.datetime.now()
            insert_query = """
            INSERT INTO Users (username, password, userType, lastName, firstName, email, phoneNumber, registrationDate, universityID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                data.get('userName', ''), hashed_password, data.get('userType', ''),
                data.get('lastName', ''), data.get('firstName', ''), data.get('email', ''),
                data.get('phoneNumber', ''), registration_date, universityID
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
    
 # Endpoint for log out
@app.route('/logout', methods=['POST'])
def logout_user():
    if current_user.is_authenticated:
        # Log out the current user
        logout_user()
        return jsonify({'message': 'User successfully logged out'})
    else:
        return jsonify({'message': 'No user is currently logged in'})
    
# Endpoint for search course 
@app.route('/searchCourse', methods=['POST'])
def search():
    try:
        data = request.get_json()
        print("Received data:", data)
        if not data:
            raise BadRequest('Invalid request data')
        cursor = db_connection.cursor()

        try:
            # Check if the courseName match
            check_query = """
                SELECT u.firstName, u.lastName, c.courseCode, c.courseName, c.yearTerm, u.universityID
                FROM Users u 
                LEFT JOIN Professor p ON u.userID = p.userID 
                LEFT JOIN course c ON p.professorID = c.professorID 
                WHERE c.courseName = %s;
            """
            cursor.execute(check_query,(data.get('courseName'),))
            result = cursor.fetchall()

            course_id_query = """
                SELECT courseID
                FROM course
                WHERE courseName = %s;
            """
            cursor.execute(course_id_query, (data.get('courseName'),))
            ids = [row[0] for row in cursor.fetchall()]
            print(ids)
            
            # print(result)
            data_list = []
            for index, row in enumerate(result):
                # Extracting values from each tuple and creating a dictionary
                data_dict = {
                    'firstName': row[0],
                    'lastName': row[1],
                    'courseCode': row[2],
                    'courseName': row[3],
                    'yearTerm': row[4],
                    'universityID': row[5],
                    'courseID': ids[index]  # Add the corresponding courseID
                }
                # Append the dictionary to the list
                data_list.append(data_dict)
                
            # print(data_list)
            cursor.close()
            return jsonify(data_list)
            
        except Exception as e:
            raise BadRequest('An error occurred while search ' + str(e))

    except BadRequest:
        raise BadRequest('Invalid request data')
    
    # Endpoint for search course 
# @app.route('/searchProfessor', methods=['POST'])
# def search():
#     try:
#         data = request.get_json()
#         print("Received data:", data)
#         if not data:
#             raise BadRequest('Invalid request data')
#         cursor = db_connection.cursor()

#         try:
#             # Check if the courseName match
#             check_query = """
#             SELECT   u.userID, u.firstName,   u.lastName,   u.userType,   u.phoneNumber,   u.email, u.universityID, p.department, p.title
#             FROM Users u 
#             LEFT JOIN Professor p ON u.userID = p.userID 
#             WHERE u.userType = "Professor" and u.firstName= %s and u.lastName= %s;  
#             """
#             cursor.execute(check_query,(data.get('firstName'),data.get('lastName')))
#             result = cursor.fetchall()

#             print(result)
#             data_list = []
#             for row in result:
#                 # Extracting values from each tuple and creating a dictionary
#                 data_dict = {
#                 'userID': row[0],
#                 'firstName': row[1],
#                 'lastName': row[2],
#                 'userType': row[3],
#                 'phoneNumber': row[4],
#                 'email': row[5],
#                 'universityID': row[6],
#                 'department': row[7],
#                 'title': row[8],
#                 }
#                 # Append the dictionary to the list
#                 data_list.append(data_dict)        
#             print(data_list)
#             cursor.close()
#             return jsonify(data_list)
            
#         except Exception as e:
#             raise BadRequest('An error occurred while search ' + str(e))

#     except BadRequest:
#         raise BadRequest('Invalid request data')
    
 # Endpoint for viewing favourite courses change user_id
@app.route('/Viewfavouritecourses', methods=['GET', 'POST'])
def view_favorite_courses():
    if request.method == 'POST':
        # Handle POST request for fetching favorite courses
        data = request.get_json()

        try:
            cursor = db_connection.cursor()
            view_query = """
            SELECT courseID FROM courseFavorite 
            WHERE userID = %s
            """
            cursor.execute(view_query, (data,))
            result = cursor.fetchall()
            print(result)

            cursor.close()
            return jsonify({'courseID': result})
        except BadRequest:
            raise BadRequest('Invalid request data')

    elif request.method == 'GET':
        # Handle GET request for initial rendering by fetching all favorite courses
        # Get the user parameter from the URL
        user = request.args.get('user')
        if not user:
            return jsonify({'error': 'User parameter is missing'})
        try:
            cursor = db_connection.cursor()
            view_all_query = """
            SELECT courseID FROM courseFavorite 
            WHERE userID = %s
            """
            cursor.execute(view_all_query, (user,)) 
            result_all = cursor.fetchall()
            courses = [item[0] for item in result_all]
            course_query = """
            SELECT * from course
            WHERE courseID = %s
            """
            res = []
            data_list = []
            for x in courses:
                cursor.execute(course_query, (x,))
                result = cursor.fetchone()
                res.append(result)
            
            for row in res:
                # Extracting values from each tuple and creating a dictionary
                data_dict = {
                'firstName': row[0],
                'lastName': row[1],
                'courseCode': row[2],
                'courseName': row[3],
                'yearTerm': row[4],
                'universityID': row[5],
                }
                # Append the dictionary to the list
                data_list.append(data_dict)
                
            print(data_list)
            cursor.close()
            return jsonify(data_list)
        except Exception as e:
            raise BadRequest('Invalid request data')

# Endpoint for adding/removing favorite courses
@app.route('/handlefavorite', methods=['POST'])
def handlefavorite():
    data = request.get_json()
    user_id = data.get('userID')
    course_id = data.get('courseID')

    try:
        cursor = db_connection.cursor()

        # Check if the combination of courseID and userID exists in the courseFavorites table
        check_query = """
        SELECT courseFavoriteID FROM courseFavorite
        WHERE courseID = %s AND userID = %s
        """
        cursor.execute(check_query, (course_id, user_id))
        existing_favorite = cursor.fetchone()

        if existing_favorite:
            # If it exists, remove it
            delete_query = """
            DELETE FROM courseFavorite
            WHERE courseFavoriteID = %s
            """
            cursor.execute(delete_query, (existing_favorite[0],))
            db_connection.commit()
            result = {'message': 'Favorite course removed'}
        else:
            # If it does not exist, add it with the courseID
            insert_query = """
            INSERT INTO courseFavorite (courseID, userID)
            VALUES (%s, %s)
            """
            cursor.execute(insert_query, (course_id, user_id))
            db_connection.commit()

            # Retrieve the generated courseFavoriteID after insertion
            select_last_insert_id_query = """
            SELECT LAST_INSERT_ID()
            """
            cursor.execute(select_last_insert_id_query)
            course_favorite_id = cursor.fetchone()[0]

            result = {'message': 'Favorite course added',
                      'courseFavoriteID': course_favorite_id}

        cursor.close()
        return jsonify(result)

    except Exception as e:
        raise BadRequest(
            'An error occurred while handling favorites: ' + str(e))
    
if __name__ == '__main__':
    app.run()

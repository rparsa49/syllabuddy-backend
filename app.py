from flask import Flask, request, jsonify, g
import mysql.connector
import datetime
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import BadRequest, Unauthorized, Conflict
import json
from email.message import EmailMessage
import ssl
import smtplib
app = Flask(__name__)

# Configure MySQL database connection
db_config = {
    'host': 'database-1.cqmz08yhaga0.us-east-2.rds.amazonaws.com',
    'user': 'admin_syllabuddy',
    'password': 'zozRun-sopgu0-gysrip',
    'database': 'syllabuddy'
}

# Enable CORS for the entire app
CORS(app)

app.secret_key = "lF!}'dcq4*,BaTH"

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, user_id, user_name, user_role):
        self.id = user_id
        self.name = user_name
        self.role = user_role

@login_manager.user_loader
def load_user(user_id, user_name, user_role):
    user = User(user_id)
    name = User(user_name)
    role = User(user_role)
    return user, name, role

def get_db():
    if 'db' not in g:
        # g.db = mysql.connector.connect(**db_config)
        g.db = mysql.connector.connect(
            host='database-1.cqmz08yhaga0.us-east-2.rds.amazonaws.com',
            port='3306',
            user='admin_syllabuddy',
            password='zozRun-sopgu0-gysrip',
            db='syllabuddy'
        )
    return g.db

@app.before_request
def before_request():
    get_db()

@app.teardown_request
def teardown_request(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Endpoint for user login
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        if not data:
            raise BadRequest('Invalid request data')

        with get_db().cursor() as cursor:
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
                        
                        role_query = """
                        SELECT userType FROM Users
                        WHERE email = %s
                        """ 
                        cursor.execute(role_query, (data.get('email', ''),))
                        role = cursor.fetchone()
                        role = role[0]
                        # Log in the user after successful login
                        user = User(user_id, name, role)
                        login_user(user)
                        return jsonify({'user_id': user_id, 'user_name': name, 'role': role, 'message': 'User successfully logged in'})

                raise Unauthorized('Incorrect email or password')

            except Exception as e:
                raise BadRequest(
                    'An error occurred while logging in: ' + str(e))

    except BadRequest:
        raise BadRequest('Invalid request data')

# Endpoint for user registration
@app.route('/register', methods=['POST'])
def register_user():
    try:
        

        data = request.get_json()
        email = data.get('email','')
        print(request.method)

        # Check if the request data is received correctly
        if not data:
            raise BadRequest('Invalid request data')

        with get_db().cursor() as cursor:
            try:
                # Check if email or phone number already exist
                check_query = """
                SELECT COUNT(*) FROM Users
                WHERE email = %s OR phoneNumber = %s
                """
                cursor.execute(check_query, (data.get(
                    'email', ''), data.get('phoneNumber', '')))
                result = cursor.fetchone()

                if result and result[0] > 0:
                    # User with the same email or phone number already exists
                    raise Conflict(
                        'An account already exists with this information. Please log in.')

                # Hash the password before storing it
                hashed_password = generate_password_hash(
                    data.get('password', ''))

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
                    data.get('userName', ''), hashed_password, data.get(
                        'userType', ''),
                    data.get('lastName', ''), data.get(
                        'firstName', ''), data.get('email', ''),
                    data.get('phoneNumber', ''), registration_date, universityID
                ))
                get_db().commit()

                # Log in the user after successful registration
                user_id = cursor.lastrowid
                user = User(user_id, data.get('firstName', ''), data.get('userType', ''))
                login_user(user)

                # Check if the user is a professor
                if data.get('userType', '') == 'professor':
                    email_sender = 'syllabuddy.wearebadatnames@gmail.com'
                    email_password = 'wqzsuxudjymfkatm'
                    email_reciever = data.get('email','')

                    subject = 'Thank you for signing up for Syllabuddy!'
                    body = """
                    Hello! Thank you for signing up for Syllabuddy we hope you enjoy your experience!

                    Username : {username}

                    password : {password}

                    """.format(username = data.get('userName',''),password = data.get('password',''))
                    em = EmailMessage()
                    em['From'] = email_sender
                    em['To']   = email_reciever
                    em['Subject'] = subject
                    em.set_content(body)

                    

                    server = smtplib.SMTP('smtp.gmail.com' ,587 ) 
                    server.starttls()
                    server.login(email_sender,email_password)
                    server.sendmail(email_sender, email_reciever,em.as_string())
                    server.quit()
                    # Insert professor information into the Professor table
                    insert_professor_query = """
                    INSERT INTO Professor (professorID, universityID, firstname, lastname, userID)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_professor_query, (
                        user_id, universityID, data.get('firstName', ''), data.get('lastName', ''), user_id))
                    get_db().commit()

                return jsonify({'message': 'User registered successfully'})

            except Exception as e:
                raise BadRequest(
                    'An error occurred while registering the user: ' + str(e))

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

        with get_db().cursor() as cursor:
            try:
                # Check if the courseName match
                # TODO: make sure only courses from the user's university are being displayed
                check_query = """
                    SELECT u.firstName, u.lastName, c.courseCode, c.courseName, c.term, u.universityID
                    FROM Users u 
                    LEFT JOIN Professor p ON u.userID = p.userID 
                    LEFT JOIN course c ON p.professorID = c.professorID 
                    WHERE c.courseName = %s;
                """
                cursor.execute(check_query, (data.get('courseName'),))
                result = cursor.fetchall()

                course_id_query = """
                    SELECT courseID
                    FROM course
                    WHERE courseName = %s;
                """
                cursor.execute(course_id_query, (data.get('courseName'),))
                ids = [row[0] for row in cursor.fetchall()]

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
                        # Add the corresponding courseID
                        'courseID': ids[index]
                    }
                    # Append the dictionary to the list
                    data_list.append(data_dict)

                return jsonify(data_list)

            except Exception as e:
                raise BadRequest(
                    'An error occurred while searching: ' + str(e))

    except BadRequest:
        raise BadRequest('Invalid request data')

<<<<<<< HEAD
# Endpoint for search course with Professor name
@app.route('/searchProfessor', methods=['POST'])
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
            SELECT   u.userID, u.firstName,   u.lastName,   u.userType,   u.phoneNumber,   u.email, u.universityID, p.department, p.title
            FROM Users u 
            LEFT JOIN Professor p ON u.userID = p.userID 
            WHERE u.userType = "Professor" and u.firstName= %s and u.lastName= %s;  
            """
            cursor.execute(check_query,(data.get('firstName'),data.get('lastName')))
            result = cursor.fetchall()

            print(result)
            data_list = []
            for row in result:
                # Extracting values from each tuple and creating a dictionary
                data_dict = {
                'userID': row[0],
                'firstName': row[1],
                'lastName': row[2],
                'userType': row[3],
                'phoneNumber': row[4],
                'email': row[5],
                'universityID': row[6],
                'department': row[7],
                'title': row[8],
                }
                # Append the dictionary to the list
                data_list.append(data_dict)        
            print(data_list)
            cursor.close()
            return jsonify(data_list)
            
        except Exception as e:
            raise BadRequest('An error occurred while search ' + str(e))

    except BadRequest:
        raise BadRequest('Invalid request data')
    
# Endpoint for viewing favourite courses change user_id

=======
# Endpoint for viewing favourite courses 
>>>>>>> upstream/main
@app.route('/Viewfavouritecourses', methods=['GET', 'POST'])
def view_favorite_courses():
    if request.method == 'POST':
        # Handle POST request for fetching favorite courses
        data = request.get_json()

        try:
            with get_db().cursor() as cursor:
                view_query = """
                SELECT courseID FROM courseFavorite 
                WHERE userID = %s
                """
                cursor.execute(view_query, (data,))
                result = cursor.fetchall()

                return jsonify({'courseID': result})

        except BadRequest:
            raise BadRequest('Invalid request data')

    elif request.method == 'GET':
        # Handle GET request for initial rendering by fetching all favorite courses
        # Get the user parameter from the URL
        user = request.args.get('user')
        if not user:
            return jsonify({'error': 'User parameter is missing'}), 400

        try:
            with get_db().cursor() as cursor:
                view_all_query = """
                SELECT courseID FROM courseFavorite 
                WHERE userID = %s
                """
                cursor.execute(view_all_query, (user,))
                result_all = cursor.fetchall()

                # Check if the result set is empty
                if not result_all:
                    return jsonify({'error': 'No favorite courses found for the user'}), 404

                ids = [item[0] for item in result_all]

                course_query = """
                    SELECT u.firstName, u.lastName, c.courseCode, c.courseName, c.term, u.universityID
                    FROM Users u 
                    LEFT JOIN Professor p ON u.userID = p.userID 
                    LEFT JOIN course c ON p.professorID = c.professorID 
                    WHERE c.courseID = %s;
                """
                res = []
                data_list = []
                for x in ids:
                    cursor.execute(course_query, (x,))
                    result = cursor.fetchall()

                    # Check if the result set is empty
                    if result:
                        res.append(result)
                    else:
                        # Handle the case when there is no data for the given course name
                        res.append(('Unknown', 'Unknown', 'Unknown',
                                   'Unknown', 'Unknown', 'Unknown'))

                    # Iterate over the outer list of lists
                for outer_list in res:
                    # Check if the outer list is not empty
                    if outer_list:
                        # Iterate over the inner list of tuples
                        for index, row in enumerate(outer_list):
                            # Create a dictionary with all information from the tuple
                            data_dict = {
                                'firstName': row[0],
                                'lastName': row[1],
                                'courseCode': row[2],
                                'courseName': row[3],
                                'yearTerm': row[4],
                                'universityID': row[5],
                            }

                        # Add the courseID key to the dictionary using the corresponding ID from the ids list
                        if index < len(ids):
                            data_dict['courseID'] = ids[index]
                        else:
                            # Handle the case when the index is out of bounds for the ids list
                            data_dict['courseID'] = 'Unknown Course ID'

                    # Append the dictionary to the list
                    data_list.append(data_dict)

                return jsonify(data_list)

        except Exception as e:
            return jsonify({'error': 'Invalid request data'}), 400

# Endpoint for adding/removing favorite courses
@app.route('/handlefavorite', methods=['POST'])
def handlefavorite():
    data = request.get_json()
    user_id = data.get('userID')
    course_id = data.get('courseID')

    try:
        with get_db().cursor() as cursor:
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
                get_db().commit()
                result = {'message': 'Favorite course removed'}
            else:
                # If it does not exist, add it with the courseID
                insert_query = """
                INSERT INTO courseFavorite (courseID, userID)
                VALUES (%s, %s)
                """
                cursor.execute(insert_query, (course_id, user_id))
                get_db().commit()

                # Retrieve the generated courseFavoriteID after insertion
                select_last_insert_id_query = """
                SELECT LAST_INSERT_ID()
                """
                cursor.execute(select_last_insert_id_query)
                course_favorite_id = cursor.fetchone()[0]

                result = {'message': 'Favorite course added',
                          'courseFavoriteID': course_favorite_id}

        return jsonify(result)

    except Exception as e:
        raise BadRequest(
            'An error occurred while handling favorites: ' + str(e))
        
# Endpoint for user to add course
@app.route('/addcourse', methods=['POST'])
def add_course():
    try:
        data = request.form
        # Check if the request data is received correctly
        if not data:
            raise BadRequest('Invalid request data')

<<<<<<< HEAD
# def down():


=======
        with get_db().cursor() as cursor:
            try:
                # Get Syllabus contents
                syllabus = request.files['syllabus']
                contents = syllabus.read()

                # Get tags data
                tags_data = data.get('tags', '')
                tags = json.loads(tags_data) if tags_data else []
                tags_json = json.dumps(tags)

                # Get UniversityID
                check_query = """
                SELECT universityID FROM Universities WHERE universityName = %s
                """
                cursor.execute(
                    check_query, (data.get('selectedUniversity', ''),))
                result = cursor.fetchall()
                if result:
                    universityID = result[0][0]

                # Get ProfessorID
                check_query = """
                SELECT professorID FROM Professor WHERE firstname = %s AND lastname = %s
                """
                cursor.execute(check_query, (data.get(
                    'profFirstname', ''), data.get('profLastname', '')))
                result = cursor.fetchall()
                if result:
                    professorID = result[0][0]
                else:
                    # Insert new professor if not found
                    insert_query = """
                    INSERT INTO Professor (professorID, universityID, firstname, lastname)
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (None, universityID, data.get(
                        'profFirstname', ''), data.get('profLastname', '')))
                    get_db().commit()

                    # Retrieve the newly inserted professorID
                    check_query = """
                    SELECT professorID FROM Professor WHERE firstname = %s AND lastname = %s
                    """
                    cursor.execute(check_query, (data.get(
                        'profFirstname', ''), data.get('profLastname', '')))
                    result = cursor.fetchall()
                    professorID = result[0][0]

                # Check if course code AT THAT UNIVERSITY already exists
                check_query = """
                SELECT COUNT(*)
                FROM course
                WHERE courseCode = %s AND universityID = %s
                """
                cursor.execute(check_query, (data.get(
                    'courseCode', ''), universityID))
                result = cursor.fetchone()

                # If no existing course is found, proceed with adding it.
                if result and result[0] > 0:
                    # course code already exists at this university
                    raise Conflict(
                        'A course already exists with this course code at this university. Please adjust your input.')

                # Insert the new course
                insert_query = """
                INSERT INTO course (courseCode, courseName, professorID, universityID, courseDescription, averageGrade, tags, term, syllabus)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    data.get('courseCode', ''),
                    data.get('courseName', ''),
                    professorID,
                    universityID,
                    data.get('courseDesc', ''),
                    data.get('averageGrade', ''),
                    tags_json,
                    data.get('term', ''),
                    contents
                ))

                get_db().commit()

                return jsonify({'message': 'Course added successfully'}), 200

            except Conflict as conflict_error:
                # Catch the specific Conflict exception and return a 409 status code
                return jsonify({'error': str(conflict_error)}), 409

            except Exception as e:
                # Handle other exceptions and return a 500 status code
                return jsonify({'error': str(e)}), 500

    except BadRequest:
        # Handle invalid request data and return a 400 status code
        return jsonify({'error': 'Invalid request data'}), 400

# Endpoint for viewing courses taught by a professor
@app.route('/viewcourses', methods=['GET'])
def view_courses():
    try:
        # Get the user parameter from the URL
        user = request.args.get('user')

        if not user:
            return jsonify({'error': 'User parameter is missing'}), 400

        with get_db().cursor() as cursor:
            try:
                # Find the professorID associated with the given userID
                professor_query = """
                SELECT professorID FROM Professor
                WHERE userID = %s
                """
                cursor.execute(professor_query, (user,))
                professor_result = cursor.fetchone()

                if not professor_result:
                    return jsonify({'error': 'No professor found for the given user'}), 404

                professor_id = professor_result[0]

                # Fetch all courses taught by the professor based on professorID
                courses_query = """
                SELECT c.courseID, c.courseCode, c.courseName, c.term
                FROM course c
                WHERE c.professorID = %s
                """
                cursor.execute(courses_query, (professor_id,))
                courses_result = cursor.fetchall()

                if not courses_result:
                    return jsonify({'courses': []})

                # Create a list of courses with necessary information
                courses = [
                    {
                        'courseID': row[0],
                        'courseCode': row[1],
                        'courseName': row[2],
                        'term': row[3],
                    }
                    for row in courses_result
                ]

                return jsonify({'courses': courses})

            except Exception as e:
                return jsonify({'error': 'An error occurred while fetching courses: ' + str(e)}), 500

    except BadRequest:
        return jsonify({'error': 'Invalid request data'}), 400
# Endpoint for user to edit course
@app.route('/editcourse', methods=['POST'])
def edit_course():
    try:
        data = request.form
        # Check if the request data is received correctly
        if not data:
            raise BadRequest('Invalid request data')

        with get_db().cursor() as cursor:
            try:
                # Get Course ID
                courseID = request.args.get('courseID')
                
                # Get Syllabus contents
                syllabus = request.files['syllabus']
                contents = syllabus.read()

                # Get tags data
                tags_data = data.get('tags', '')
                tags = json.loads(tags_data) if tags_data else []
                tags_json = json.dumps(tags)

                # Get UniversityID
                check_query = """
                SELECT universityID FROM Universities WHERE universityName = %s
                """
                cursor.execute(
                    check_query, (data.get('selectedUniversity', ''),))
                result = cursor.fetchall()
                if result:
                    universityID = result[0][0]

                # Get ProfessorID
                check_query = """
                SELECT professorID FROM Professor WHERE firstname = %s AND lastname = %s
                """
                cursor.execute(check_query, (data.get(
                    'profFirstname', ''), data.get('profLastname', '')))
                result = cursor.fetchall()
                if result:
                    professorID = result[0][0]
                else:
                    # Insert new professor if not found
                    insert_query = """
                    INSERT INTO Professor (professorID, universityID, firstname, lastname)
                    VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (None, universityID, data.get(
                        'profFirstname', ''), data.get('profLastname', '')))
                    get_db().commit()

                    # Retrieve the newly inserted professorID
                    check_query = """
                    SELECT professorID FROM Professor WHERE firstname = %s AND lastname = %s
                    """
                    cursor.execute(check_query, (data.get(
                        'profFirstname', ''), data.get('profLastname', '')))
                    result = cursor.fetchall()
                    professorID = result[0][0]

                # Insert the new course information 
                update_query = """
                UPDATE course
                SET courseCode = %s, courseName = %s, professorID = %s, universityID = %s, courseDescription = %s, averageGrade = %s, tags = %s, term = %s, syllabus = %s
                WHERE courseID = %s;
                """
                cursor.execute(update_query, (
                    data.get('courseCode', ''),
                    data.get('courseName', ''),
                    professorID,
                    universityID,
                    data.get('courseDesc', ''),
                    data.get('averageGrade', ''),
                    tags_json,
                    data.get('term', ''),
                    contents,
                    courseID
                ))

                get_db().commit()

                return jsonify({'message': 'Course changed successfully'}), 200

            except Conflict as conflict_error:
                # Catch the specific Conflict exception and return a 409 status code
                return jsonify({'error': str(conflict_error)}), 409

            except Exception as e:
                # Handle other exceptions and return a 500 status code
                return jsonify({'error': str(e)}), 500

    except BadRequest:
        # Handle invalid request data and return a 400 status code
        return jsonify({'error': 'Invalid request data'}), 400
>>>>>>> upstream/main
if __name__ == '__main__':
    app.run()
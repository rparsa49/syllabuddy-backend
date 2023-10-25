from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, Flask!'

# endpoint for user registration
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    return jsonify({'message': 'User registered successfully'})

if __name__ == '__main__':
    app.run()

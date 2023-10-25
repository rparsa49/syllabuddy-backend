# Syllabuddy Backend

The Syllabuddy Backend is the server-side component of the Syllabuddy application, which facilitates the registration of users and provides endpoints for interacting with the Syllabuddy database. This README provides an overview of the backend, its setup, and basic usage.

## Features

The Syllabuddy Backend provides the following features:
- User registration and login functionality.
- API endpoints for managing user data.
- Secure communication with the Syllabuddy frontend.

## Prerequisites

Before you begin, ensure you have met the following requirements:
* Python 3.x installed.
* Python package manager, pip, installed.
* A database management system (e.g., PostgreSQL, MySQL) set up and configured.

## Getting Started
### Installation
1. Clone the Syllabuddy Backend repository to your local machine:
```
git clone https://github.com/yourusername/syllabuddy-backend.git
cd syllabuddy-backend
```
2. Install the required Python packages using pip:
```
pip install -r requirements.txt
```

## API Endpoints
The Syllabuddy Backend provides the following API endpoints:
* `/register` - User registration.
* `/login` - User login.
* `/user/{user_id}` - User details by user ID.

## Usage

To run the backend, execute the following command:
```
flask run
```
The backend will start, and it will be accessible at http://localhost:5000/.

## License

This project is licensed under the MIT License. 


from flask import request, jsonify

from socialbox import app
from socialbox.helpers import database, passwords

@app.route("/api/register", methods=['POST'])
def register():
    """Endpoint to register users."""

    # Get POST information from request
    username = request.values.get('username', None)
    firstname = request.values.get('firstname', None)
    surname = request.values.get('surname', None)
    email = request.values.get('email', None)
    password = request.values.get('password', None)

    # Checks that all required information to sign up has been provided
    if not all([username, firstname, surname, email, password]):
        return jsonify({"ok": False, "message": "All fields need a value."})

    # Checks that the username provided doesn't already have an account
    if database.get_user(username):
        return jsonify({"ok": False, "message": "Username already exists in system."})

    # Creates a user in the database, returning the new API Key
    api_key = database.create_user(username, firstname, surname, email, password)

    # Return a success message with the new API Key
    return jsonify({"ok": True, "api_key": api_key})


@app.route("/api/login", methods=['POST'])
def login():
    """Endpoint to login users."""

    # Get POST information from request
    username = request.values.get('username', None)
    password = request.values.get('password', None)

    # Checks that both a username and password has been provided
    if not all([username, password]):
        return jsonify({"ok": False, "message": "Both username and password need a value."})

    # Get's the user object from the database
    user = database.get_user(username)

    # If the user cannot be found, an error message is returned
    if not user:
        return jsonify({"ok": False, "message": "Username not found in system."})

    password_hash = user["password_hash"]

    # Verifies that supplied password matches the stored password hash
    if not passwords.verify_password(password, password_hash):
        return jsonify({"ok": False, "message": "Incorrect password."})

    api_key = database.update_api_key(user['username'])
    user['api_key'] = api_key

    user['scores'] = database.get_user_scores(user['username'])

    # Return success message with the user's API Key
    return jsonify({"ok": True, **user})


@app.route("/api/add_friend", methods=['POST'])
def add_friend():
    """Endpoint to add a friend."""

    # Get POST information from request
    api_key = request.values.get('api_key', None)
    friend_username = request.values.get('friend_username', None)

    # Ensures that both an API Key and friend's username is provided
    if not all([api_key, friend_username]):
        return jsonify({"ok": False, "message": "API Key and friend's username must be provided."})

    # Gets the user with the supplied API Key
    user = database.verify_api_key(api_key)

    # If no user is found, an error message is passed back to the client
    if not user:
        return jsonify({"ok": False, "message": "API Key provided is not valid."})

    # Get the user with given username
    friend = database.get_user(friend_username)

    # If the username already exists, provide error message
    if not friend:
        return jsonify({"ok": False, "message": "Friend's username provided is not valid."})

    database.add_friend(user, friend)

    return jsonify(dict({"ok": True}))


@app.route("/api/get_friends", methods=['POST'])
def get_friends():
    """Endpoint to list all friends."""

    # Get POST information from request
    api_key = request.values.get('api_key', None)

    # Ensures that both an API Key and trip ID is provided
    if not api_key:
        return jsonify({"ok": False, "message": "API Key must be provided."})


    # Gets the user with the supplied API Key
    user = database.verify_api_key(api_key)

    # If no user is found, an error message is passed back to the client
    if not user:
        return jsonify({"ok": False, "message": "API Key provided is not valid."})

    friends = []

    # Include each friend's score data in the response
    for user in user['friends']:
        friend = {
            'username': user,
            'scores': database.get_user_scores(user)
        }

        friends.append(friend)

    return jsonify(dict({"ok": True, 'friends': friends}))
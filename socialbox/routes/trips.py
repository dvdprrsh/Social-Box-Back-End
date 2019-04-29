from flask import request, jsonify
from maya import MayaDT

from socialbox import app
from socialbox.helpers import database


@app.route("/api/begin_trip", methods=['POST'])
def begin_trip():
	"""Endpoint to begin a trip."""

	# Get POST information from request
	api_key = request.values.get('api_key', None)

	# Checks that supplied API Key belongs to a user
	user = database.verify_api_key(api_key)

	if not user:
		return jsonify({"ok": False, "message": "API Key provided is not valid."})

	# Create a new trip belonging to the user with the supplied API Key
	trip_id = database.create_trip(user["username"])

	# Return success message with supplied API Key
	return jsonify({"ok": True, "trip_id": trip_id})


@app.route("/api/update_trip", methods=['POST'])
def update_trip():
	"""Endpoint to update a trip's data."""

	# Get POST information from request
	api_key = request.values.get('api_key', None)
	trip_id = request.values.get('trip_id', None)
	lat = request.values.get('lat', None)
	long = request.values.get('long', None)
	timestamps = request.values.get('timestamp', None)


	# Checks that all required information to begin a trip has been provided
	if not all([api_key, trip_id, lat, long, timestamps]):
		return jsonify({"ok": False, "message": "API Key, Lat, Long and Timestamps must be provided."})

	# Ensures that the same number of lat and long ordinates has been passed
	if len(lat.split(',')) != len(long.split(',')) != len(timestamps.split(',')):
		return jsonify({"ok": False, "message": "Number of lat ordinates, long co-ordinates and timestamps must be the same."})

	# Gets the user with the supplied API Key
	user = database.verify_api_key(api_key)

	# If no user is found, an error message is passed back to the client
	if not user:
		return jsonify({"ok": False, "message": "API Key provided is not valid."})

	# Gets the trip object with the supplied trip ID
	trip = database.get_trip(trip_id)

	# If the trip_id supplied doesn't represent a real trip, an error message is returned
	if not trip:
		return jsonify({"ok": False, "message": "Trip ID provided is not valid."})

	# If the user making the request doesn't own the trip, an error message is returned
	if not database.does_user_own_trip(user['username'], trip_id):
		return jsonify({"ok": False, "message": "Trip does not belong to you."})

	# Append the new lat, long and timestamp data to the object
	database.update_trip(trip_id, lat, long, timestamps)

	# Calculate the trip's scores using 'TripScorer'
	database.calculate_scores(trip_id)

	# Obtain updated trip data
	trip = database.get_trip(trip_id)

	# Return a success response
	return jsonify({"ok": True, **trip})



@app.route("/api/get_all_trips", methods=['POST'])
def get_all_trips():
	"""Endpoint to list all a user's trips."""

	# Get POST information from request
	api_key = request.values.get('api_key', None)

	# Checks that all required information to begin a trip has been provided
	if not api_key:
		return jsonify({"ok": False, "message": "API Key must be provided."})

	# Gets the user with the supplied API Key
	user = database.verify_api_key(api_key)

	# If no user is found, an error message is passed back to the client
	if not user:
		return jsonify({"ok": False, "message": "API Key provided is not valid."})

	trips = database.get_all_trips(user['username'])

	return jsonify(dict({"ok": True}, trips=trips))

@app.route("/api/get_trip_detail", methods=['POST'])
def get_trip_detail():
	"""Endpoint to get a trip's details."""

	# Get POST information from request
	api_key = request.values.get('api_key', None)
	trip_id = request.values.get('trip_id', None)

	# Checks that all required information to begin a trip has been provided
	if not all([api_key, trip_id]):
		return jsonify({"ok": False, "message": "API Key and trip ID must be provided."})

	# Gets the user with the supplied API Key
	user = database.verify_api_key(api_key)

	# If no user is found, an error message is passed back to the client
	if not user:
		return jsonify({"ok": False, "message": "API Key provided is not valid."})

	# Gets the trip object with the supplied trip ID
	trip = database.get_trip(trip_id)

	# If the trip_id supplied doesn't represent a real trip, an error message is returned
	if not trip:
		return jsonify({"ok": False, "message": "Trip ID provided is not valid."})

	# If the user making the request doesn't own the trip, an error message is returned
	if not database.does_user_own_trip(user['username'], trip_id):
		return jsonify({"ok": False, "message": "Trip does not belong to you."})

	# Include a 'slang time' such as '1 day ago' in the response
	slang_time = MayaDT(trip["start_time"]).slang_time()

	return jsonify(dict(ok=True, slang_time=slang_time, **trip))


from time import time
from bson.objectid import ObjectId
from collections import defaultdict

from maya import MayaDT

from socialbox import mongo
from socialbox.helpers.passwords import hash_password, generate_api_key
from socialbox.helpers.trip_scorer import TripScorer

# Initialise pointers to mongodb tables
users = mongo.db.users
trips = mongo.db.trips

def create_user(username, firstname, surname, email, password):
	"""Function to create a new user document."""

	api_key = generate_api_key()

	user = {
		'username': username,
		'firstname': firstname,
		'surname': surname,
		'email': email,
		'password_hash': hash_password(password),
		'api_key': api_key,
		'friends': [],
	}

	users.insert_one(user)
	return api_key

def get_user(username):
	"""Function to get an existing user document by username."""

	result = users.find_one({'username': username}, {'_id': 0})
	return result

def verify_api_key(api_key):
	"""Function to check a given API Key matches an user document."""

	result = users.find_one({'api_key': api_key})
	return result

def update_api_key(username):
	"""Function to generate a new API Key for a user document."""

	api_key = generate_api_key()
	users.update({'username': username}, {'$set': {'api_key': api_key}})
	return api_key

def create_trip(username):
	"""Function to create a new trip document with a given username."""

	trip = {
		'username': username,
		'start_time': time(),
		'lat': [],
		'long': [],
		'timestamps': [],
		'score': {},
	}

	_trip = trips.insert_one(trip)
	return str(_trip.inserted_id)

def get_trip(trip_id):
	"""Function to get a trip document with a given trip_id."""

	result = trips.find_one({'_id': ObjectId(trip_id)})

	# Convert ObjectID object to a string for serialisation
	if result:
		result['_id'] = str(result['_id'])

	return result

def get_all_trips(username):
	"""Function to get a trip document with a given trip_id."""

	result = list(trips.find({'username': username}))

	# Include a 'slang time' such as '1 day ago' in the response
	for trip in result:
		trip['_id'] = str(trip['_id'])
		trip['slang_time'] = MayaDT(trip["start_time"]).slang_time()

	return result

def does_user_own_trip(username, trip_id):
	"""Function to check if a given username owns a trip."""

	trip = trips.find_one({'_id': ObjectId(trip_id)})

	if trip:
		return username == trip['username']
	else:
		return False

def update_trip(trip_id, lat, long, timestamps):
	"""Function to update a trip object with new lat, long and timestamp data."""

	trip = trips.find_one({'_id': ObjectId(trip_id)})

	# Split comma delimited string into lists
	lat = lat.split(',')
	long = long.split(',')
	timestamps = timestamps.split(',')

	trips.update(
		{'_id': ObjectId(trip_id)},
		{'$push': {'lat': {'$each': lat}}}
	)

	trips.update(
		{'_id': ObjectId(trip_id)},
		{'$push': {'long': {'$each': long}}}
	)

	trips.update(
		{'_id': ObjectId(trip_id)},
		{'$push': {'timestamps': {'$each': timestamps}}}
	)


def is_friends(user, friend):
	"""Function to calculate whether two user objects are friends."""

	return (user['username'] in friend['friends'] or
			friend['username'] in user['friends'])

def add_friend(user, friend):
	"""Function to calculate whether two user objects are friends."""

	users.update({'username': user['username']}, {'$push': {'friends': friend['username']}})

def calculate_scores(trip_id):
	"""Function to calculate the scores of a given trip."""

	trip = get_trip(trip_id)
	trip_scorer = TripScorer(trip['lat'], trip['long'], trip['timestamps'])

	scores = trip_scorer.score_trip()

	trips.update({'_id': ObjectId(trip_id)}, {"$set": { "scores": scores}})

def get_user_scores(username):
	"""Function to get a user's average scores over all of their trips."""

	_trips = trips.find({'username': username})
	scores = defaultdict(int)
	n = 0

	for trip in _trips:
		if trip.get('scores', None):
			n += 1

			for type, score in trip['scores'].items():
				scores[type] += score

	for key in scores:
		scores[key] /= n

	return scores

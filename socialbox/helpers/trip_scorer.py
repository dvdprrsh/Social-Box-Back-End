from collections import defaultdict
from datetime import datetime, date

from geopy.distance import geodesic
from suntime import Sun
from pint import UnitRegistry


ureg = UnitRegistry()

class Coord:
	"""Object to represent a recorded point in a trip with
		a lattiude ordinate, longitude ordinate and a timestamp"""

	def __init__(self, lat, long, timestamp):
		self.lat = lat
		self.long = long
		self.timestamp = timestamp

	def as_tuple(self):
		return (self.lat, self.long)


class TripScorer:
	"""Object to handle scoring a trip object"""

	def __init__(self, lats=[], longs=[], timestamps=[]):
		# Convert JSON strings to floats
		self.lats = [float(lat) for lat in lats]
		self.longs = [float(long) for long in longs]

		# Convert JSON exp string to float
		self.timestamps = [float(timestamp)/1000 for timestamp in timestamps]

		self.speeds = []
		self.scores = {}

		# Checks to see that all required data has been provided
		if lats and longs and timestamps:
			# Calculate sunrise and sunset time on the day that the trip started
			sunrise_timestamp = Sun(self.lats[0], self.longs[0]) \
								.get_sunrise_time(date.fromtimestamp(self.timestamps[0])) \
								.timestamp()

			sunset_timestamp = Sun(self.lats[0], self.longs[0]) \
								.get_sunset_time(date.fromtimestamp(self.timestamps[0])) \
								.timestamp()

			self.sunrise = datetime.fromtimestamp(sunrise_timestamp).time()
			self.sunset = datetime.fromtimestamp(sunset_timestamp).time()

	def score_trip(self):
		'''Function to give a trip a score for all four categories'''

		if self.lats and self.longs and self.timestamps:
			# Generate a list of speeds in mph for the given points in the trip
			if not self.speeds:
				self._generate_speeds()

			# Generate all categories scores
			self.scores['time_of_day'] = self._time_of_day()
			self.scores['acceleration'] = self._acceleration()
			self.scores['braking'] = self._braking()
			self.scores['speeding'] = self._speeding()

			return self.scores
		else:
			# If the required data isn't given, just return a dict defaulted to 0 (int())
			return defaultdict(int)


	def _time_of_day(self):
		'''Function to score the 'time of day' category'''
		total = 0

		# Counts the number of points that were recorded after sunset and before sunrise
		for timestamp in self.timestamps:
			if self.__is_timestamp_daytime(timestamp):
				total += 1

		# Return the proportion of instances when driving after sunset compared to n points recorded
		return int(100 * total / len(self.timestamps))

	def __is_timestamp_daytime(self, timestamp):
		'''Helper function to work out of a given timestamp is before or after sunset'''

		timestamp = datetime.fromtimestamp(timestamp).time()
		return timestamp >= self.sunrise and timestamp <= self.sunset

	def _acceleration(self):
		'''Function to score the 'acceleration' category'''

		current = next = ()
		total = 0

		# Records the number of times that a user's speed is doubled in one time frame
		# Loop through speeds in pairs (for current and next)
		for i in range(len(self.speeds) - 1):
			current, next = self.speeds[i:i+2]

			if next.magnitude <= current.magnitude * 2:
				total += 1

		# Return the proportion of extreme acceleration instances compared to n points recorded
		return int(100 * total / len(self.speeds))

	def _braking(self):
		'''Function to score the 'braking' category'''

		current = next = ()
		total = 0

		# Records the number of times that a user's speed is halved in one time frame
		# Loop through speeds in pairs (for current and next)
		for i in range(len(self.speeds) - 1):
			current, next = self.speeds[i:i+2]
			if next.magnitude / 2 <= current.magnitude:
				total += 1

		# Return the proportion of extreme braking instances compared to n points recorded
		return int(100 * total / len(self.speeds))

	def _speeding(self):
		'''Function to score the 'speeding' category'''

		total = 0

		# Records the number of times that a user's speed is over 70mph
		for speed in self.speeds:
			if speed.magnitude > 70:
				total += 1

		# Return the proportion of speeding instances compared to n points recorded
		return int((100 * (len(self.speeds) - total) / len(self.speeds)))

	def _generate_speeds(self):
		current = next = ()
		self.speeds = []

		# Calculates speed using s = d/t
		# Loop through timestamps in pairs (for current and next)
		for i in range(len(self.timestamps) - 1):
			# Get current and next coords, creating Coord objects
			current = Coord(self.lats[i], self.longs[i], self.timestamps[i])
			next = Coord(self.lats[i + 1], self.longs[i + 1], self.timestamps[i + 1])

			# Calculates time elapsed (default ~1 second) with pint's unit reg library recording unit as second
			time = (next.timestamp - current.timestamp) * ureg.second

			# Using GeoPy to use a geodesic method to calculate the distance (in miles) between two GPS points
			distance = geodesic(current.as_tuple(), next.as_tuple()).miles * ureg.mile

			# Calculate speed between two points (using speed = distance/time)
			speed = (distance / time).to(ureg.mile / ureg.hour)

			# Append the speed to the list of speeds
			self.speeds.append(speed)

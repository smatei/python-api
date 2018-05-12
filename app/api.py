import re
from pymongo import MongoClient, TEXT
from bson import ObjectId
from bson.errors import InvalidId
from flask_restful import abort


class ApiUtils:
    configuration = None

    def __init__(self, configuration):
        self.configuration = configuration

    def song_list(self, page_size_str, page_num_str):
        """ Returns a list of songs with some details on them. Paginate."""

        # validate page size
        try:
            page_size = int(page_size_str)
        except ValueError:
            abort(404, message="page size must be an positive integer, value is " + page_size_str)

        if page_size <= 0:
            abort(404, message="page size must be an positive integer, value is " + page_size_str)

        # validate page number
        try:
            page_num = int(page_num_str)
        except ValueError:
            abort(404, message="page number must be an positive integer, value is " + page_num_str)

        if page_num <= 0:
            abort(404, message="page number must be an positive integer, value is " + page_num_str)

        mongo_connection = MongoConnection(self.configuration)
        collection = mongo_connection.get_songs_collection()

        data = []

        # Calculate number of documents to skip
        skips = page_size * (page_num - 1)

        for document in collection.find().skip(skips).limit(page_size):
            data.append(document)

        mongo_connection.close()

        return data

    def song_avg_difficulty(self, level_str):
        """Takes an optional parameter "level" to select only songs from a specific level.
            Returns the average difficulty for all songs."""
        # validate level
        try:
            level = int(level_str)
        except ValueError:
            abort(404, message="level must be an positive integer, value is " + level_str)

        if level <= 0:
            abort(404, message="level must be an positive integer, value is " + level_str)

        mongo_connection = MongoConnection(self.configuration)
        totals_collection = mongo_connection.get_songs_totals_collection()

        # from the totals collection get the single document
        # and then find the selected level (count and sum)
        # from the count and sum compute the average
        #
        # {'_id': ...,
        # 'level':
        #   {'13': {'count': 5, 'difficulty_sum': 70.48},
        #   '9': {'count': 3, 'difficulty_sum': 29.08},
        #   '3': {'count': 1, 'difficulty_sum': 2},
        #   '6': {'count': 2, 'difficulty_sum': 12}
        # }}
        document = totals_collection.find_one()

        # some levels may be missing from level totals document
        # return 0 for average
        if level_str not in document['level']:
            return {'average': 0.0}

        count = document['level'][level_str]['count']
        difficulty = document['level'][level_str]['difficulty_sum']

        if count == 0:
            return {'average': 0.0}

        return {'average': difficulty/count}

    def song_search(self, message):
        """Takes in parameter a 'message' string to search.
            Return a list of songs. The search should take into account song's artist and title.
            The search should be case insensitive."""

        mongo_connection = MongoConnection(self.configuration)
        collection = mongo_connection.get_songs_collection()

        data = []

        # search for exact matches first
        # keep artist and title lowercase too so that we can search case insensitive
        for document in collection.find({'$or': [{'artist_lowercase': message.lower()},
                                                 {'title_lowercase': message.lower()}]}).limit(100):
            data.append(document)

        # if found nothing for exact match, search for "contains"
        if len(data) == 0:
            # limit search to 100 elements
            # if we want more, we can either increase the length of the search message to make it more specific
            # or add a pagination (but this is out of specs now)
            for document in collection.find({'$or': [{'artist_lowercase': re.compile(message.lower())},
                                                     {'title_lowercase': re.compile(message.lower())}]}).limit(100):
                data.append(document)

        mongo_connection.close()

        return data

    def song_rating(self, song_id, rating_str):
        """Takes in parameter a "song_id" and a "rating"
           This call adds a rating to the song. Ratings should be between 1 and 5.

           returns {"n": 1, "nModified": 1, "ok": 1.0, "updatedExisting": true} if id exists
           returns {"n": 0, "nModified": 0, "ok": 1.0, "updatedExisting": false} if id does not exists"""

        # validate rating
        try:
            rating = int(rating_str)
        except ValueError:
            abort(404, message="rating must be an integer between 1 and 5, value is " + rating_str)

        if rating < 1 or rating > 5:
            abort(404, message="rating must be an integer between 1 and 5")

        mongo_connection = MongoConnection(self.configuration)
        collection = mongo_connection.get_songs_collection()

        # keep a field rating for each song and when we want to add a rating
        # we increment the count for the rating index
        # 'rating': {'4': {'count': 1}, '5': {'count': 1}}
        document = collection.update({"_id": ObjectId(song_id)}, {'$inc': {'rating.' + str(rating) + '.count': 1}})

        mongo_connection.close()

        return document

    def song_avg_rating(self, song_id):
        """Returns the average, the lowest and the highest rating of the given song id."""

        # validate song_id
        try:
            object_id = ObjectId(song_id)
        except InvalidId:
            abort(404, message="song id is not valid: " + song_id)

        mongo_connection = MongoConnection(self.configuration)
        collection = mongo_connection.get_songs_collection()

        document = collection.find_one({"_id": object_id})

        mongo_connection.close()

        if document is None:
            abort(404, message="the song with id " + song_id + "is missing")

        # if no rating for the song, return 0
        if 'rating' not in document:
            return {'average': 0.0}

        # if we have ratings for the song
        # 'rating': {'4': {'count': 1}, '5': {'count': 1}}
        # iterate all the possible ratings (some may be missing, if so, continue)
        # and get sum and count, with that, get the average
        rating = document['rating']
        total_count = 0
        total_rating = 0
        for index in range(5):
            if str(index + 1) not in rating:
                continue
            rating_index = rating[str(index + 1)]
            if rating is None:
                continue
            count = rating_index['count']
            total_rating += count * (index + 1)
            total_count += count

        if total_count == 0:
            average = 0
        else:
            average = float(total_rating) / float(total_count)

        return {'average': average}

    def init_db_data(self):
        """cleanup test collection and insert the test data"""
        mongo_connection = MongoConnection(self.configuration)

        # create/cleanup the songs collection
        song_collection = mongo_connection.get_songs_collection()
        song_collection.remove({})

        # create/cleanup the levels collection
        level_collection = mongo_connection.get_songs_totals_collection()
        level_collection.remove({})

        import os

        with open(os.path.join(os.path.dirname(__file__), 'data.json'), 'rb') as f:
            data_json = f.read().decode('utf8')
            from bson import json_util
            data = json_util.loads(data_json)

            song_collection.insert_many(data)

            # index by artist_lowercae and title_lowercae
            song_collection.create_index([('artist_lowercase', TEXT), ('title_lowercase', TEXT)],
                                         name='artist_title_index')

            # save level totals (count and sum for each level)
            # this will be a collection with only one element
            # {'_id': ...,
            # 'level':
            #   {'13': {'count': 5, 'difficulty_sum': 70.48},
            #   '9': {'count': 3, 'difficulty_sum': 29.08},
            #   '3': {'count': 1, 'difficulty_sum': 2},
            #   '6': {'count': 2, 'difficulty_sum': 12}
            # }}
            # this will help us compute song_avg_difficulty
            inserted_id = level_collection.insert_one({"level": {}}).inserted_id
            for index in range(len(data)):
                level = data[index]['level']
                difficulty = data[index]['difficulty']
                level_collection.update({"_id": ObjectId(inserted_id)},
                                        {'$inc': {'level.' + str(level) + '.count': 1}})
                level_collection.update({"_id": ObjectId(inserted_id)},
                                        {'$inc': {'level.' + str(level) + '.difficulty_sum': difficulty}})

        mongo_connection.close()

        return {"setup": "done"}


class MongoConnection:
    mongo_client = None
    mongo_db = None

    def __init__(self, configuration):
        self.mongo_client = MongoClient(configuration['DATABASE_URL'])
        self.mongo_db = self.mongo_client.get_database(configuration['DATABASE'])

    def get_songs_collection(self):
        return self.mongo_db.get_collection('songs')

    def get_songs_totals_collection(self):
        return self.mongo_db.get_collection('songs_totals')

    def close(self):
        self.mongo_client.close()

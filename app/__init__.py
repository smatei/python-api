from flask import Flask, request, make_response
from flask_restful import Api, Resource
from app.api import ApiUtils
from bson.json_util import dumps


def create_app(config_file=None):
    """Create and configure an instance of the Songs application."""
    app = Flask(__name__)

    if config_file is None:
        app.config.from_pyfile('dev.cfg', silent=True)
    else:
        app.config.from_pyfile(config_file, silent=True)

    configuration = app.config

    api = Api(app)
    api_utils = ApiUtils(configuration)

    @api.representation('application/json')
    def output_json(obj, code, headers=None):
        """
        This is needed because we need to use a custom JSON converter
        that knows how to translate MongoDB types to JSON.
        """
        resp = make_response(dumps(obj), code)
        resp.headers.extend(headers or {})

        return resp

    class SongList(Resource):
        def get(self, page_size, page_num):
            return api_utils.song_list(page_size, page_num)

    api.add_resource(SongList, '/songs/<page_size>/<page_num>')

    class SongAvgDifficulty(Resource):
        def get(self, level):
            return api_utils.song_avg_difficulty(level)

    api.add_resource(SongAvgDifficulty, '/songs/avg/difficulty/<level>')

    class SongSearch(Resource):
        def get(self, message):
            return api_utils.song_search(message)

    api.add_resource(SongSearch, '/songs/search/<message>')

    class SongRating(Resource):
        def post(self):
            json_data = request.get_json(force=True)
            song_id = json_data['song_id']
            rating = json_data['rating']
            return api_utils.song_rating(song_id, rating)

    api.add_resource(SongRating, '/songs/rating')

    class SongAvgRating(Resource):
        def get(self, song_id):
            return api_utils.song_avg_rating(song_id)

    api.add_resource(SongAvgRating, '/songs/avg/rating/<song_id>')

    class InitDatabase(Resource):
        def get(self):
            return api_utils.init_db_data()

    api.add_resource(InitDatabase, '/setup/test/data')

    return app


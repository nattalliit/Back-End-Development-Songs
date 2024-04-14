from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, Response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route('/health', methods=['GET'])
def health_check():
    data = {'status': 'OK'}
    response = make_response(jsonify(data), 200)
    
    response.headers['Server'] = 'Werkzeug/2.2.2 Python/3.7.16'
    response.headers['Date'] = 'Wed, 08 Feb 2023 16:37:14 GMT'
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Length'] = len(response.data)
  
    
    return response

if __name__ == '__main__':
    app.run(debug=True)


@app.route('/count', methods=['GET'])
def count():
    """Return length of data"""
    count = db.songs.count_documents({})
    
    return jsonify({"count": count}), 200



from flask import Response

@app.route('/song', methods=['GET'])
def get_songs():
    # Retrieve all documents from the 'songs' collection
    all_songs = list(db.songs.find({}))

    # Format the data as required
    songs_json = json_util.dumps({"songs": all_songs})

    # Create a response with the JSON data and set appropriate headers
    response = Response(songs_json, status=200, mimetype='application/json')
    response.headers['Server'] = 'Werkzeug/2.2.2 Python/3.7.16'
    response.headers['Date'] = 'Thu, 09 Feb 2023 02:22:09 GMT'
    response.headers['Content-Length'] = len(songs_json)

    return response



@app.route('/song/<string:song_id>', methods=['GET'])
def get_song_by_id(song_id):
    # Retrieve the song document from the 'songs' collection by its ID
    song = db.songs.find_one({"id": int(song_id)})

    # Check if the song exists
    if song is None:
        abort(404, description=f"Song with ID {song_id} not found")

    # Format the data as required
    song_json = json_util.dumps(song)

    # Create a response with the JSON data and set appropriate headers
    response = Response(song_json, status=200, mimetype='application/json')
    response.headers['Server'] = 'Werkzeug/2.2.2 Python/3.7.16'
    response.headers['Date'] = 'Thu, 09 Feb 2023 02:23:59 GMT'
    response.headers['Content-Length'] = len(song_json)

    return response



@app.route('/song/<int:song_id>', methods=['PUT'])
def update_song(song_id):
    # Extract song data from the request body
    updated_song_data = request.json

    # Check if a song with the provided ID exists
    existing_song = db.songs.find_one({"id": song_id})
    if existing_song is None:
        # If the song does not exist, return a 404 response
        return jsonify({"message": f"Song with ID {song_id} not found"}), 404

    # Update the song in the database
    db.songs.update_one({"id": song_id}, {"$set": updated_song_data})

    # Return a success message
    return jsonify({"message": "Song updated successfully"}), 200




@app.route('/song/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    # Delete the song from the database
    delete_result = db.songs.delete_one({"id": song_id})

    # Check if the song was found and deleted
    if delete_result.deleted_count == 0:
        # If the song was not found, return a 404 response
        return jsonify({"message": "Song not found"}), 404
    else:
        # If the song was successfully deleted, return a 204 response
        return "", 204

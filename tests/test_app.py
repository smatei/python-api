import json
import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app('test.cfg')

    client = app.test_client()

    # cleanup test collection and insert the test data
    apicall = client.get('/setup/test/data')
    print(apicall.data)

    yield client


def test_song_list(client):
    print("test_song_list")

    """ Paginate with page size 10. For test data we should have
        10 results on page 1,
        1 result on page 2, and
        0 results on page 3"""

    apicall = client.get('/songs/10/1')
    assert apicall.status_code == 200

    data = json.loads(apicall.data)
    assert len(data) == 10

    apicall = client.get('/songs/10/2')
    assert apicall.status_code == 200

    data = json.loads(apicall.data)
    assert len(data) == 1

    apicall = client.get('/songs/10/3')
    assert apicall.status_code == 200

    data = json.loads(apicall.data)
    assert len(data) == 0


def test_song_search(client):
    print("test_song_search")

    # search that does not find anything
    apicall = client.get('/songs/search/blablabla')
    assert apicall.status_code == 200

    data = json.loads(apicall.data)
    assert len(data) == 0

    # search with exact match
    apicall = client.get('/songs/search/alabama sunrise')
    assert apicall.status_code == 200

    data = json.loads(apicall.data)
    assert len(data) == 1

    # search with two matches
    apicall = client.get('/songs/search/al')
    assert apicall.status_code == 200

    data = json.loads(apicall.data)
    assert len(data) == 2


def test_song_rating(client):
    print("test_song_rating")

    # test incorrect rating parameter 20
    apicall = client.post('songs/rating', json={"song_id": "111111111111111111111111", "rating": 20})
    assert apicall.status_code == 404

    # test incorrect rating parameter blabla
    apicall = client.post('songs/rating', json={"song_id": "111111111111111111111111", "rating": "blabla"})
    assert apicall.status_code == 404

    # test missing song id
    apicall = client.post('songs/rating', json={"song_id": "111111111111111111111111", "rating": 1})
    assert apicall.status_code == 200
    data = json.loads(apicall.data)
    assert data['updatedExisting'] is False

    # test existing id, first we have to get one with find song
    apicall = client.get('/songs/search/alabama sunrise')
    data = json.loads(apicall.data)
    song_id = data[0]['_id']['$oid']

    apicall = client.post('songs/rating', json={"song_id": song_id, "rating": 1})
    assert apicall.status_code == 200
    data = json.loads(apicall.data)
    assert data['updatedExisting'] is True


def test_song_avg_rating(client):
    print("test_song_avg_rating")

    # test missing song id
    apicall = client.get('songs/avg/rating/111111111111111111111111')
    assert apicall.status_code == 404

    # test existing song id without any ratings, first we have to get one with find song
    apicall = client.get('/songs/search/alabama sunrise')
    data = json.loads(apicall.data)
    song_id = data[0]['_id']['$oid']

    apicall = client.get('songs/avg/rating/' + song_id)
    assert apicall.status_code == 200
    data = json.loads(apicall.data)
    assert data['average'] == 0.0

    # test existing song id with ratings, but first we have to add ratings
    client.post('songs/rating', json={"song_id": song_id, "rating": 4})
    client.post('songs/rating', json={"song_id": song_id, "rating": 5})

    apicall = client.get('songs/avg/rating/' + song_id)
    assert apicall.status_code == 200
    data = json.loads(apicall.data)
    assert data['average'] == 4.5


def test_song_avg_difficulty(client):
    print("test_song_avg_difficulty")

    # test invalid negative level
    apicall = client.get('songs/avg/difficulty/-1')
    assert apicall.status_code == 404

    # test invalid non integer level
    apicall = client.get('songs/avg/difficulty/blabla')
    assert apicall.status_code == 404

    # test valid non existing level
    apicall = client.get('songs/avg/difficulty/7')
    assert apicall.status_code == 200
    data = json.loads(apicall.data)
    assert data['average'] == 0

    # test valid existing level
    apicall = client.get('songs/avg/difficulty/6')
    assert apicall.status_code == 200
    data = json.loads(apicall.data)
    assert data['average'] == 6


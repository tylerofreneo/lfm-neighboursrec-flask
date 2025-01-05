import os
import sys
import pickle
import joblib
import requests
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sklearn.neighbors import KNeighborsRegressor

def get_recs(user) :
    _input_user = user

    # Gets usernames from last.fm site into list
    try :
        response = requests.get(f"https://last.fm/user/{_input_user}/neighbours")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        usernames = list(map(lambda x: x.text, soup.find_all(class_ = 'user-list-link link-block-target'))) 
    except Exception as e :
        raise e

    # Perhaps, give popular recs
    if (len(usernames) <= 25) :
        raise Exception("Not enough recent scrobbles to give recommendations.")

    # Load api key from .env
    load_dotenv()
    LFM_API_KEY = os.environ['LFM_API_KEY']

    def get_tracks(method, user, limit = 1000) :
        # method is one of: getTop[Albums|Artists|Tracks], getRecentTracks, getWeekly[Albums|Artists|Tracks]
        url = f"http://ws.audioscrobbler.com/2.0/?method=user.{method}&user={user}&api_key={LFM_API_KEY}&format=json&limit={limit}"
        try :
            response = requests.get(url)
            response.raise_for_status()
            tracks = (pd.json_normalize(response.json()['toptracks']['track']))
            return tracks
        except Exception as e :
            raise e

    # Get top tracks from all neighbours
    acc = get_tracks("getTopTracks", usernames[0]).assign(user = usernames[0], similarity_rank = 1)
    for user in usernames[1:] :
        try : 
            tracks = get_tracks("getTopTracks", user).assign(user = user, similarity_rank = usernames.index(user) + 1)
            acc = pd.concat([acc, tracks])
        except Exception as e :
            continue    
    neighbours_songs = (
        acc.assign(song = lambda x: x['name'] +' - ' +  x['artist.name'])
        [["mbid", "artist.mbid", "@attr.rank", "similarity_rank", "playcount", "song", "user"]]
    )
    neighbours_songs['playcount'] = pd.Series(map(lambda x: int(x), neighbours_songs['playcount']))
    neighbours_songs['rating'] = pd.qcut(neighbours_songs['playcount'], q = 5,
                                        labels = [1, 2, 3, 4, 5]).astype(int)
    neighbours_songs['@attr.rank'] = neighbours_songs['@attr.rank'].astype(int)
    neighbours_songs_grouped = neighbours_songs.groupby('song').agg({'@attr.rank' : 'mean', 'similarity_rank' : 'mean', 'playcount' : 'mean', 'rating' : 'mean', 'user' : 'count'})
    neighbours_songs_filtered = neighbours_songs_grouped[neighbours_songs_grouped['user'] >= 10]
    # Load model from file
    with open('knn.pkl', 'rb') as file:  
        knn = pickle.load(file)

    # Get list of input user tracks 
    _input_user_tracks = get_tracks("getTopTracks", _input_user).assign(user = _input_user, similarity_rank = 1)
    _input_user_tracks = (
        _input_user_tracks.assign(song = lambda x: x['name'] +' - ' +  x['artist.name'])
        ['song']
    )

    # Get recommendations
    recommendations = neighbours_songs_filtered.assign(predicted = knn.predict(
        neighbours_songs_filtered[['@attr.rank', 'similarity_rank', 'user']]
        ))
    recommendations = recommendations.sort_values('predicted', ascending = False).reset_index()
    recommendations = recommendations[~recommendations['song'].isin(_input_user_tracks)]
    return recommendations['song'].head(30).to_list()
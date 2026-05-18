from flask import Flask, render_template, request, redirect, session
import pandas as pd
import pickle
import requests
import json
import os

app = Flask(__name__)

app.secret_key = "movie_secret"

# TMDB API KEY
TMDB_API_KEY = "YOUR_TMDB_API_KEY"

# Load datasets
movies = pd.read_csv('data/movies.csv')
ratings = pd.read_csv('data/ratings.csv')

# Load similarity matrix
similarity = pickle.load(open('model/similarity.pkl', 'rb'))

# Top Rated Movies
movie_ratings = ratings.groupby('movieId')['rating'].mean().reset_index()

movie_ratings = movie_ratings.merge(
    movies,
    on='movieId'
)

top_movies = movie_ratings.sort_values(
    by='rating',
    ascending=False
).head(12)

# Fetch Poster
def fetch_poster(movie_name):

    try:

        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"

        response = requests.get(url)

        data = response.json()

        if data['results']:

            poster_path = data['results'][0]['poster_path']

            if poster_path:
                return "https://image.tmdb.org/t/p/w500/" + poster_path

    except:
        pass

    return ""

# Recommendation Function
def recommend(movie):

    movie = movie.lower().strip()

    movies['lower_title'] = movies['title'].str.lower()

    # partial matching
    matched_movies = movies[
        movies['lower_title'].str.contains(movie, na=False)
    ]

    if matched_movies.empty:
        return [], []

    movie_index = matched_movies.index[0]

    distances = similarity[movie_index]

    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:7]

    recommended_movies = []
    posters = []

    for i in movie_list:

        movie_title = movies.iloc[i[0]].title

        recommended_movies.append(movie_title)

        posters.append(fetch_poster(movie_title))

    return recommended_movies, posters

# LOGIN PAGE
@app.route('/login', methods=['GET', 'POST'])

def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if os.path.exists('users.json'):

            with open('users.json', 'r') as f:

                users = json.load(f)

                if username in users and users[username] == password:

                    session['user'] = username

                    return redirect('/')

        return "Invalid Credentials"

    return render_template('login.html')

# REGISTER PAGE
@app.route('/register', methods=['GET', 'POST'])

def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        users = {}

        if os.path.exists('users.json'):

            with open('users.json', 'r') as f:
                users = json.load(f)

        users[username] = password

        with open('users.json', 'w') as f:
            json.dump(users, f)

        return redirect('/login')

    return render_template('register.html')

# HOME PAGE
@app.route('/')

def home():

    if 'user' not in session:
        return redirect('/login')

    return render_template(
        'index.html',
        top_movies=top_movies
    )

# RECOMMENDATION
@app.route('/recommend', methods=['POST'])

def recommend_movies():

    movie = request.form['movie']

    recommendations, posters = recommend(movie)

    if not recommendations:

        return render_template(
            'result.html',
            recommendations=[],
            posters=[],
            searched_movie=movie,
            error="Movie not found"
        )

    return render_template(
        'result.html',
        recommendations=recommendations,
        posters=posters,
        searched_movie=movie,
        error=""
    )

# WATCHLIST
@app.route('/watchlist', methods=['GET', 'POST'])

def watchlist():

    if 'user' not in session:
        return redirect('/login')

    username = session['user']

    file_path = f'watchlists/{username}.json'

    if request.method == 'POST':

        movie = request.form['movie']

        watchlist = []

        if os.path.exists(file_path):

            with open(file_path, 'r') as f:
                watchlist = json.load(f)

        watchlist.append(movie)

        with open(file_path, 'w') as f:
            json.dump(watchlist, f)

    watchlist = []

    if os.path.exists(file_path):

        with open(file_path, 'r') as f:
            watchlist = json.load(f)

    return render_template(
        'watchlist.html',
        movies=watchlist
    )

# LOGOUT
@app.route('/logout')

def logout():

    session.pop('user', None)

    return redirect('/login')

# RUN APP
if __name__ == '__main__':

    app.run(debug=True)
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import pickle

movies = pd.read_csv('data/movies.csv')
ratings = pd.read_csv('data/ratings.csv')

merged = pd.merge(ratings, movies, on='movieId')

movie_matrix = merged.pivot_table(
    index='userId',
    columns='title',
    values='rating'
)

movie_matrix = movie_matrix.fillna(0)

similarity = cosine_similarity(movie_matrix.T)

pickle.dump(similarity, open('model/similarity.pkl', 'wb'))

print("Model Trained Successfully!")
from .models import Favorite, User, Movie


def add_or_delete_favorite(user_id, hentai_code):
    user = User.get(User.telegram_id == user_id)
    movie = Movie.get(Movie.code == hentai_code)

    favorite, created = Favorite.get_or_create(user=user, movie=movie)

    if not created:
        favorite.delete_instance()


def get_favorites_for_user(user_id: int):
    query = Favorite.select().join(User).where(User.telegram_id == user_id)
    return [(favorite.movie.code, favorite.movie.title) for favorite in query]


def is_movie_in_favorites(user_id, movie_code: int | str) -> bool:
    movie_code = int(movie_code)
    query = Favorite.select().join(User).where(User.telegram_id == user_id)

    for fav in query:
        if fav.movie.code == movie_code:
            return True
    return False


def delete_movie_from_favorites(movie_code: int):
    query = Favorite.select().join(Movie).where(Movie.code == movie_code)
    for favorite in query:
        print(favorite.movie.title, favorite.movie.code)
        favorite.delete_instance()

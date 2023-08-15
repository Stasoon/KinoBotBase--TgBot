from typing import Generator

from peewee import fn

from .models import Movie
from .favorite import delete_movie_from_favorites


def add_movie(code: int | str, title: str, description: str, url: str, photo_id: str = None) -> int:
    try:
        new_movie = Movie(code=code, title=title, description=description, photo_id=photo_id, url=url)
        new_movie.save()
        return new_movie.id
    except Exception as e:
        print(e)


def get_movie_by_code_or_none(code: int) -> dict[str, str, str, str] | None:
    movie = Movie.get_or_none(Movie.code == code)

    return {
            'code': movie.code,
            'title': movie.title,
            'description': movie.description,
            'photo': movie.photo_id,
            'url': movie.url
            } if movie else None


def get_random_movie_code():
    random_index = Movie.select().order_by(fn.Random()).first().code
    return random_index


def get_fresh_movies(count: int):
    yield from ((movie.code, movie.title) for movie in Movie.select().order_by(Movie.id.desc()).limit(count))


def get_all_movies() -> Generator:
    yield from ((movie.code, movie.title) for movie in Movie.select())


def delete_movie_by_code(code: int) -> bool:
    try:
        delete_movie_from_favorites(code)
        Movie.get_or_none(Movie.code == code).delete_instance()
    except AttributeError:
        return False
    else:
        return True

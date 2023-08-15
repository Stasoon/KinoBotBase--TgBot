from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, \
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from src.database.favorite import get_favorites_for_user, is_movie_in_favorites
from src.database.movie import get_movie_by_code_or_none, get_fresh_movies
from src.misc import movies_callback, favorite_nav_callback


class Keyboards:
    # region Subchecking

    check_sub_button = InlineKeyboardButton('❓ Проверить ❓', callback_data='checksubscription')

    @classmethod
    def get_not_subbed_markup(cls, channels_to_sub_data) -> InlineKeyboardMarkup | None:
        if len(channels_to_sub_data) == 0:
            return None

        cahnnels_markup = InlineKeyboardMarkup(row_width=1)
        [
            cahnnels_markup.add(InlineKeyboardButton(channel_data.get('title'), url=channel_data.get('url')))
            for channel_data in channels_to_sub_data
        ]
        cahnnels_markup.add(cls.check_sub_button)
        return cahnnels_markup

    # endregion

    @staticmethod
    def get_fake_menu() -> InlineKeyboardMarkup:
        search_by_code = InlineKeyboardButton('🎥 Найти название 🎥', callback_data='fake_menu')
        watch_movie = InlineKeyboardButton('🍿 Смотреть фильм 🍿', callback_data='fake_menu')
        return InlineKeyboardMarkup(row_width=1).add(search_by_code, watch_movie)

    @staticmethod
    def get_menu() -> ReplyKeyboardMarkup:
        search_by_code = KeyboardButton('🔎 Искать по коду')
        random_movie = KeyboardButton('🎲 Случайный фильм')
        fresh = KeyboardButton('🔥 Новинки')
        favorite = KeyboardButton('⭐ Избранное')

        return ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)\
            .add(search_by_code)\
            .insert(random_movie).insert(fresh).insert(favorite)

    @staticmethod
    def get_back_markup() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton('✖Отменить', callback_data='back'))

    @staticmethod
    def get_movies_markup(user_id, movie_code: int | str) -> InlineKeyboardMarkup:
        movie = get_movie_by_code_or_none(movie_code)
        movie_markup = InlineKeyboardMarkup(row_width=1)

        if movie.get('url'):
            watch_button = InlineKeyboardButton('👀 Смотреть', url=movie.get('url'))
            movie_markup.add(watch_button)

        favorites = is_movie_in_favorites(user_id, movie_code)
        already_in_favorites = favorites

        favorite_button = InlineKeyboardButton(
            text='❌ Удалить из избранного' if already_in_favorites else '⭐ В Избранное',
            callback_data=movies_callback.new(action='favorite', code=movie_code)
        )

        movie_markup.add(favorite_button)
        return movie_markup

    @classmethod
    def get_fresh(cls) -> InlineKeyboardMarkup:
        one_page_count = 10
        markup = InlineKeyboardMarkup(row_width=1)

        for movie in get_fresh_movies(one_page_count):
            markup.add(cls.__get_movie_button(movie[0], movie[1]))

        return markup

    @classmethod
    def get_favorites_page(cls, user_id: int, page_num: int = 1) -> InlineKeyboardMarkup | None:
        favorites = get_favorites_for_user(user_id)
        if len(favorites) < 1:
            return None

        one_page_count = 5
        pages_count = ((len(favorites) - 1) // one_page_count) + 1

        if page_num > pages_count:
            page_num = pages_count

        markup = InlineKeyboardMarkup()
        for fav in favorites[page_num*one_page_count-one_page_count : page_num*one_page_count]:
            markup.row(cls.__get_movie_button(code=fav[0], title=fav[1]))
        cls.__add_footer_buttons(markup, page_num, pages_count)

        return markup

    @staticmethod
    def __get_movie_button(code, title) -> InlineKeyboardButton:
        return InlineKeyboardButton(text=title, callback_data=movies_callback.new('show', code))

    @staticmethod
    def __add_footer_buttons(markup: InlineKeyboardMarkup, current_page_num: int, total_pages_count: int) -> None:
        next_button = InlineKeyboardButton('Далее ➡', callback_data=favorite_nav_callback.new('next', current_page_num))
        back_button = InlineKeyboardButton('⬅ Назад', callback_data=favorite_nav_callback.new('back', current_page_num))

        counter_button = InlineKeyboardButton(f'📖 {current_page_num}/{total_pages_count}', callback_data='counter')

        if total_pages_count == 1:
            markup.add(counter_button)
        elif 1 < current_page_num < total_pages_count:
            markup.add(back_button, counter_button, next_button)
        elif current_page_num < total_pages_count:
            markup.add(counter_button, next_button)
        else:
            markup.add(back_button, counter_button)





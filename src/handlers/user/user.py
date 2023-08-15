from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageNotModified

from src.create_bot import bot
from src.database.user import create_user
from src.database.movie import get_movie_by_code_or_none, get_random_movie_code
from src.database.favorite import add_or_delete_favorite
from src.database.reflink import increase_op_count
from src.utils import send_typing_action, throttle
from src.utils.check_sub import get_notsubbed_channels_markup_or_none
from src.misc import movies_callback, favorite_nav_callback, MovieSearching
from .messages import Messages
from .kb import Keyboards


async def send_hentai(code: int, user_id: int) -> bool:
    hentai_data = get_movie_by_code_or_none(code)

    if hentai_data:
        title = hentai_data.get('title')
        descript = hentai_data.get('description')
        photo = hentai_data.get('photo')

        if not photo:
            await send_hentai_without_photo(title, descript, code, user_id=user_id)
        else:
            await send_hentai_with_photo(title, descript, photo, code, user_id=user_id)
        return True

    await bot.send_message(chat_id=user_id, text=Messages.get_movie_not_found(code),
                           reply_markup=Keyboards.get_menu())
    return False


async def send_hentai_without_photo(title, descript, code, user_id):
    await bot.send_message(
        chat_id=user_id,
        text=Messages.get_formatted_movie_description(title=title, description=descript),
        reply_markup=Keyboards.get_movies_markup(user_id, movie_code=code)
    )


async def send_hentai_with_photo(title, descript, photo, code, user_id):
    await bot.send_photo(
        chat_id=user_id,
        caption=Messages.get_formatted_movie_description(title=title, description=descript),
        photo=photo,
        reply_markup=Keyboards.get_movies_markup(user_id, movie_code=code)
    )


async def send_menu(to_message: types.Message):
    await to_message.answer(Messages.get_menu(), reply_markup=Keyboards.get_menu())


# region Handlers

@throttle()
async def __handle_start_command(message: types.Message) -> None:
    await send_typing_action(message)
    create_user(telegram_id=message.from_id,
                name=message.from_user.username or message.from_user.full_name,
                reflink=message.get_full_command()[1])

    await message.answer(text=Messages.get_welcome(message.from_user.first_name), reply_markup=Keyboards.get_fake_menu())


@throttle(rate=1.5)
async def __handle_fake_menu_callback(callback: types.CallbackQuery):
    await callback.answer()
    await send_menu(callback.message)


# !!! ПРОВЕРКА ПОДПИСКИ !!! #
@throttle()
async def __handle_search_by_code_button(message: types.Message, state: FSMContext):
    await send_typing_action(message)

    await message.answer(Messages.get_search_by_code(), reply_markup=Keyboards.get_back_markup())
    await state.set_state(MovieSearching.wait_for_code)


async def __handle_code_message(message: types.Message, state: FSMContext) -> None:
    await send_typing_action(message)

    if message.text.isdigit():
        code = int(message.text)
        await send_hentai(code, message.from_user.id)
    else:
        await message.answer(Messages.get_code_incorrect(), reply_markup=Keyboards.get_back_markup())
        return
    await state.finish()


async def __handle_back_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await send_menu(callback.message)
    await state.finish()


# !!! ПРОВЕРКА ПОДПИСКИ !!! #
@throttle(rate=1)
async def __handle_random_hentai_button(message: types.Message):
    await send_typing_action(message)

    hentai_random_code = get_random_movie_code()
    await send_hentai(hentai_random_code, message.from_user.id)


# !!! ПРОВЕРКА ПОДПИСКИ !!! #
@throttle(rate=1)
async def __handle_fresh_hentai_button(message: types.Message):
    await send_typing_action(message)
    await message.answer(Messages.get_fresh(), reply_markup=Keyboards.get_fresh())


# !!! ПРОВЕРКА ПОДПИСКИ !!! #
@throttle()
async def __handle_show_favorites_button(message: types.Message):
    await send_typing_action(message)

    markup = Keyboards.get_favorites_page(message.from_user.id)
    if markup:
        await message.answer(Messages.get_favorite(), reply_markup=markup)
    else:
        await message.answer(Messages.get_favorite_empty())


async def __handle_show_favorite_hentai_callback(callback: types.CallbackQuery, callback_data: movies_callback):
    await callback.message.delete()
    await send_hentai(callback_data.get('code'), callback.from_user.id)


async def __handle_favorites_navigation_callback(callback: types.CallbackQuery, callback_data: favorite_nav_callback):
    page_num = int(callback_data.get('current_page_number'))

    if callback_data.get('direction') == 'next':
        page_num += 1
    else:
        page_num -= 1

    markup = Keyboards.get_favorites_page(user_id=callback.from_user.id, page_num=page_num)
    await callback.message.edit_reply_markup(reply_markup=markup)


async def __handle_hentai_favorite_callback(callback: types.CallbackQuery, callback_data: movies_callback) -> None:
    code = callback_data.get('code')
    user_id = callback.from_user.id

    add_or_delete_favorite(user_id, code)
    new_markup = Keyboards.get_movies_markup(user_id, code)
    try:
        await callback.message.edit_reply_markup(reply_markup=new_markup)
    except MessageNotModified:
        pass


async def __handle_not_sub_messages(message: types.Message):
    await send_typing_action(message)

    markup = await get_notsubbed_channels_markup_or_none(message.bot, message.from_user.id)
    if markup:
        await message.answer(text=Messages.get_not_sub(), reply_markup=markup)


@throttle(rate=1.3)
async def __handle_checksub_callback(callback: types.CallbackQuery) -> None:
    new_markup = await get_notsubbed_channels_markup_or_none(callback.bot, callback.from_user.id)

    if not new_markup:
        await callback.message.edit_text('✅ Готово! \nМожете пользоваться ботом 😉')
        increase_op_count(callback.from_user.id)
        await callback.message.answer(text=Messages.get_menu())
    else:
        await callback.answer('Вы не подписались на некоторые каналы! ☹')
        if new_markup != callback.message.reply_markup:
            await callback.message.edit_text(text=Messages.get_not_sub(), reply_markup=new_markup)


async def __handle_unexpected_messages(message: types.Message):
    await message.answer(Messages.get_unexpected(), reply_markup=Keyboards.get_menu())

# endregion


def register_user_handlers(dp: Dispatcher) -> None:
    # обработка команды /start
    dp.register_message_handler(__handle_start_command, commands=['start'])

    # обработка кнопок фейкового меню
    dp.register_callback_query_handler(__handle_fake_menu_callback, text='fake_menu')

    # нажатие на кнопку проверки подписки
    dp.register_message_handler(__handle_not_sub_messages, is_sub=False)
    dp.register_callback_query_handler(__handle_checksub_callback,
                                       text=Keyboards.check_sub_button.callback_data)

    # обработка поиска фильма по коду
    dp.register_message_handler(__handle_search_by_code_button, text='🔎 Искать по коду', state=None)
    dp.register_message_handler(__handle_code_message, content_types=['text'], state=MovieSearching.wait_for_code)
    dp.register_callback_query_handler(__handle_back_callback, text='back', state=MovieSearching.wait_for_code)

    # обработка нажатия на рандом
    dp.register_message_handler(__handle_random_hentai_button, text='🎲 Случайный фильм')

    # обработка нажатия на Новинки
    dp.register_message_handler(__handle_fresh_hentai_button, text='🔥 Новинки')

    # обработка нажатия на Избранное
    dp.register_message_handler(__handle_show_favorites_button, text='⭐ Избранное')
    dp.register_callback_query_handler(__handle_favorites_navigation_callback, favorite_nav_callback.filter())
    dp.register_callback_query_handler(__handle_show_favorite_hentai_callback, movies_callback.filter(action='show'))
    # удаление / добавление в избранное
    dp.register_callback_query_handler(__handle_hentai_favorite_callback, movies_callback.filter(action='favorite'))

    # незапланированные сообщения
    dp.register_message_handler(__handle_unexpected_messages, content_types=['any'])

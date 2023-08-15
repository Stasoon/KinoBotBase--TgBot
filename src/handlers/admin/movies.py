from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

from src.misc.admin_states import MovieStates
from src.database.movie import add_movie, delete_movie_by_code, get_all_movies, get_movie_by_code_or_none


movie_callback_data = CallbackData('movie', 'action')


class Keyboards:
    reply_button_for_admin_menu = KeyboardButton('🎥 Фильмы 🎥')
    movie = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton('➕ Добавить фильм', callback_data=movie_callback_data.new('add')),
        InlineKeyboardButton('➖ Удалить фильм', callback_data=movie_callback_data.new('del')),
        InlineKeyboardButton('👀 Список фильмов', callback_data=movie_callback_data.new('list'))
    )
    cancel_markup = InlineKeyboardMarkup()\
        .add(InlineKeyboardButton('🔙 Отмена', callback_data=movie_callback_data.new(action='cancel')))

    skip_markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton('Пропустить ➡', callback_data=movie_callback_data.new(action='skip'))
    )


class Utils:
    @staticmethod
    async def get_url_from_message(message: Message):
        url = None

        for item in message.entities or ():
            if item.type == 'url':
                url = item.get_text(message.text)
                break

        return url

    @staticmethod
    async def save_movie(state: FSMContext):
        data = await state.get_data()

        add_movie(
            code=data.get('code'),
            title=data.get('title'),
            description=data.get('description'),
            photo_id=data.get('photo'),
            url=data.get('url')
        )
    #
    # @staticmethod
    # async def send_message_by_state(to_message: Message, state: FSMContext, markup: InlineKeyboardMarkup = None):
    #     match await state.get_state():
    #         case MovieStates.wait_for_code:
    #             await to_message.answer("✏ Отправьте название фильма: ")
    #         case MovieStates.wait_for_description:
    #             await to_message.a



class Handlers:
    @staticmethod
    async def show_menu(to_message: Message):
        await to_message.answer('Что вы хотите сделать?',
                                reply_markup=Keyboards.movie)

    @staticmethod
    async def __handle_admin_movie_button(message: Message):
        await Handlers.show_menu(message)

    @staticmethod
    async def __handle_add_movie_callback(callback: CallbackQuery, state: FSMContext):
        await callback.message.delete()
        await callback.message.answer("💯 Отправьте код нового фильма: ",
                                      reply_markup=Keyboards.cancel_markup)
        await state.set_state(MovieStates.wait_for_code)

    @staticmethod
    async def __handle_movie_code(message: Message, state: FSMContext):
        if not message.text.isdigit():
            await message.answer('❗Отправленное сообщение не является числом. Попробуйте ещё раз:',
                                 reply_markup=Keyboards.cancel_markup)
            return

        if not get_movie_by_code_or_none(message.text):
            await state.update_data(code=message.text)
            await message.answer('✏ Отправьте название фильма: ')
            # await Utils.send_message_by_state(to_message=message, state=state)
            await state.set_state(MovieStates.wait_for_title)
        else:
            await message.answer('❗Фильм с таким кодом уже добавлен. Выберите другой код:',
                                 reply_markup=Keyboards.cancel_markup)

    @staticmethod
    async def __handle_movie_title(message: Message, state: FSMContext):
        await state.update_data(title=message.text)

        await message.answer(f'📝 Теперь пришлите описание:')
        await state.set_state(MovieStates.wait_for_description)

    @staticmethod
    async def __handle_movie_description(message: Message, state: FSMContext):
        await state.update_data(description=message.text)

        await message.answer('🔗 Пришлите ссылку, по которой можно посмотреть фильм:')
        await state.set_state(MovieStates.wait_for_url)

    @staticmethod
    async def __handle_movie_url(message: Message, state: FSMContext):
        url = await Utils.get_url_from_message(message)

        if not url:
            await message.answer('❗Вы ввели не ссылку. Попробуйте снова:', reply_markup=Keyboards.cancel_markup)
            return

        await state.update_data(url=url)
        await message.answer('🖼 Отправьте фото:', reply_markup=Keyboards.skip_markup)
        await state.set_state(MovieStates.wait_for_photo)

    @staticmethod
    async def __handle_movie_photo(message: Message, state: FSMContext):
        if not message.photo:
            await message.answer('❗Это не фото. Попробуйте снова:', reply_markup=Keyboards.skip_markup)
            return

        await state.update_data(photo=message.photo[0].file_id)

        await Utils.save_movie(state)
        await message.answer('✅ Фильм добавлен.')
        await state.finish()

    @staticmethod
    async def __handle_skip_callback(callback: CallbackQuery, state: FSMContext):
        await callback.message.delete()

        await Utils.save_movie(state)
        await state.finish()
        await callback.message.answer('✅ Фильм добавлен.')

    @staticmethod
    async def __handle_delete_movie_callback(callback: CallbackQuery, state: FSMContext):
        await callback.message.delete()
        await callback.message.answer('🔘 Пришлите код фильма, который хотите удалить:',
                                      reply_markup=Keyboards.cancel_markup)
        await state.set_state(MovieStates.wait_for_code_to_delete)

    @staticmethod
    async def __handle_movie_code_to_delete(message: Message, state: FSMContext):
        if delete_movie_by_code(message.text):
            await message.answer(f'❌ Фильм с кодом <code>{message.text}</code> удалён')
            await state.finish()
        else:
            await message.answer(f'❗ Фильм с кодом <code>{message.text}</code> не существует, попробуйте ещё раз:')

    @staticmethod
    async def __handle_movie_list_callback(callback: CallbackQuery):
        await callback.message.delete()
        text = '<b>Список добавленных фильмов:</b>\n\n'

        for code, description in get_all_movies():
            text += f'<code>{code}</code> — {description} \n'

        if text == '':
            await callback.message.answer('Вы не добавили ни один фильм.', reply_markup=Keyboards.cancel_markup)
        else:
            await callback.message.answer(text, reply_markup=Keyboards.cancel_markup)

    @staticmethod
    async def __handle_cancel_callback(callback: CallbackQuery, state: FSMContext):
        await callback.message.delete()
        await Handlers.show_menu(to_message=callback.message)
        await state.finish()

    @classmethod
    def register_movie_handlers(cls, dp: Dispatcher):
        dp.register_message_handler(cls.__handle_admin_movie_button, is_admin=True,
                                    text=Keyboards.reply_button_for_admin_menu.text)

        # Добавление хентая
        dp.register_callback_query_handler(cls.__handle_add_movie_callback,
                                           movie_callback_data.filter(action='add'),
                                           state=None)
        dp.register_message_handler(cls.__handle_movie_code, is_admin=True, state=MovieStates.wait_for_code)
        dp.register_message_handler(cls.__handle_movie_title, is_admin=True, state=MovieStates.wait_for_title)
        dp.register_message_handler(cls.__handle_movie_description, is_admin=True,
                                    state=MovieStates.wait_for_description)
        dp.register_message_handler(cls.__handle_movie_url, is_admin=True, state=MovieStates.wait_for_url)
        dp.register_message_handler(cls.__handle_movie_photo, is_admin=True, state=MovieStates.wait_for_photo,
                                    content_types=['text', 'photo'])
        dp.register_callback_query_handler(cls.__handle_skip_callback,
                                           movie_callback_data.filter(action='skip'),
                                           is_admin=True,
                                           state=MovieStates.wait_for_photo)

        # удаление хентая
        dp.register_callback_query_handler(cls.__handle_delete_movie_callback,
                                           movie_callback_data.filter(action='del'),
                                           state=None)
        dp.register_message_handler(cls.__handle_movie_code_to_delete, is_admin=True,
                                    state=MovieStates.wait_for_code_to_delete)

        # список хентая
        dp.register_callback_query_handler(cls.__handle_movie_list_callback, movie_callback_data.filter(action='list'))

        #
        dp.register_callback_query_handler(cls.__handle_cancel_callback,
                                           movie_callback_data.filter(action='cancel'),
                                           state='*')

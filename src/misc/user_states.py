from aiogram.dispatcher.filters.state import State, StatesGroup


class SubscriptionChecking(StatesGroup):
    wait_for_check_button = State()


class MovieSearching(StatesGroup):
    wait_for_code = State()
    wait_for_name = State()

from ..data import User, JobFair
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)
from ..staff import utils


# @utils.time_check
def update_user(call: CallbackQuery, user_list, ejf_list, only_one=False):
    is_selected, interest_index = call.data.split(";")[2:4]

    if only_one and interest_index:
        user_list.clear()
        user_list.append(ejf_list[int(interest_index)])
        return

    for index, interest in enumerate(ejf_list):
        if interest_index == str(index):
            if is_selected == "0":  # not yet exists
                user_list.append(interest)
            else:
                user_list.remove(interest)
            break


# @utils.time_check
def create_interests_markup(user: User, col_number: int = 2):
    all_interests = JobFair.objects.first().filters_interest

    interest_markup = InlineKeyboardMarkup()

    for row in inline_keyboard_columns_generator(
        callback_action="Interests",
        user_list=user.interests,
        ejf_list=all_interests,
        col=col_number,
    ):
        interest_markup.add(*row)

    return interest_markup


def create_experience_markup(user: User, col_number: int = 3):
    all_experience = JobFair.objects.first().filters_experience

    experience_markup = InlineKeyboardMarkup()

    for row in inline_keyboard_columns_generator(
        callback_action="Experience",
        user_list=user.experience,
        ejf_list=all_experience,
        col=col_number,
    ):
        experience_markup.add(*row)

    return experience_markup


def create_employment_markup(user: User, col_number: int = 3):
    all_employment = JobFair.objects.first().filters_employment

    employment_markup = InlineKeyboardMarkup()

    for row in inline_keyboard_columns_generator(
        callback_action="Employment",
        user_list=user.employment,
        ejf_list=all_employment,
        col=col_number,
    ):
        employment_markup.add(*row)

    return employment_markup


def form_user_interests_callback(
    action: str,
    is_selected: int,
    index: int,
):
    return f"User;{action};{is_selected};{index};Edit"


def inline_keyboard_columns_generator(
    callback_action: str, user_list: list, ejf_list: list, col=2
):
    row = []

    for index, btn_name in enumerate(ejf_list, 1):
        is_selected = 0
        if btn_name in user_list:
            btn_name += " ✅"
            is_selected = 1

        btn_callback = form_user_interests_callback(
            callback_action, is_selected, index - 1
        )

        row += [InlineKeyboardButton(btn_name, callback_data=btn_callback)]

        if index % col == 0:
            yield row
            row = []

    if row:
        yield row

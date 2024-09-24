from src.data import Data, User

from src.sections.admin import AdminSection
from src.sections.hr import HRSection
from src.sections.user import UserSection
from src.sections.job_fair import JobFairSection

from src.staff.updates import Updater
from src.staff import utils

from src.objects import quiz

import configparser
from telebot import TeleBot, logger

import test_bot

import logging, os

logger.setLevel(logging.INFO)

logger.info("Initializing settings")

config = configparser.ConfigParser()
config.read("Settings.ini")

logger.info("Settings read")

API_TOKEN = (
    os.environ.get("TOKEN", False)
    if os.environ.get("TOKEN", False)
    else config["TG"]["token"]
)
CONNECTION_STRING = (
    os.environ.get("DB", False)
    if os.environ.get("DB", False)
    else config["Mongo"]["db"]
)

bot = TeleBot(API_TOKEN, parse_mode="HTML")
data = Data(conn_string=CONNECTION_STRING, bot=bot)

logger.info("Connected to db")

admin_section = AdminSection(data=data)
hr_section = HRSection(data=data)
user_section = UserSection(data=data)
job_fair_section = JobFairSection(data=data)

updater = Updater()


@bot.message_handler(commands=["start"])
def start_bot(message):
    user = updater.update_user_interaction_time(message)

    # If it is the first start
    try:
        if user.additional_info is None:
            send_welcome_message_and_start_quiz(user)

        # If in Job Fair mode
        # TODO fix it later
        # elif user.last_interaction_date < data.JOB_FAIR_END_TIME:
        #    job_fair_section.send_start_menu(user)

        # If user is HR
        elif user.hr_status is True:
            hr_section.send_start_menu(user=user)

        # If user is basic user
        else:
            # job_fair_section.send_start_menu(user)
            user_section.send_start_menu(user=user)

    except Exception as e:
        print(f"Exception during start - {e}")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    user = updater.update_user_interaction_time(call.message)
    bot.clear_step_handler_by_chat_id(user.chat_id)
    section = call.data.split(";")[0]

    try:
        if section == "User":
            user_section.process_callback(call=call, user=user)

        elif section == "HR":
            hr_section.process_callback(call=call, user=user)

        elif section == "Admin":
            admin_section.process_callback(call=call, user=user)

        elif section == "DELETE":
            utils.delete_message(bot=bot, call=call)

        elif section == "IGNORE":
            bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Exception during {section}.{call.data.split(';')[1]} btn tap - {e}")


@bot.message_handler(content_types=["text"])
def handle_text_buttons(message):
    user = updater.update_user_interaction_time(message)
    message_text = message.text

    try:

        # User buttons
        if message_text in user_section.TEXT_BUTTONS:
            user_section.process_text(message_text, user)

        # JobFair buttons
        elif message_text in job_fair_section.TEXT_BUTTONS:
            job_fair_section.process_text(message_text, user)

        # Call admin menu
        elif message_text == data.ADMIN_PASSWORD:
            admin_section.send_admin_menu(user=user)

        # Trigger special commands
        elif message_text.startswith("ejf__"):
            test_bot.process_tests_text(
                bot, user, data, message_text, user_section.send_start_menu
            )

        # log in HR to Company
        elif message_text.startswith("login_"):
            hr_section.register_hr(user, login_str=message_text)

        # TEMP: change bot type
        elif message.text == "affnpafbnarcuibraicpairfbiryfg":
            utils._temp_change_bot_mode(user_section)

        else:
            pass  # answer user that it was invalid input (in utils.py maybe)

    except Exception as e:
        print(e)


@bot.message_handler(content_types=["document"])
def test_save_cv(message):
    user = updater.update_user_interaction_time(message)
    chat_id = user.chat_id

    file_id = message.document.file_id
    file_name = message.document.file_name
    file_size = message.document.file_size

    if file_size > 1024 ** 2 * 5:
        bot.send_message(chat_id, text="Приймаю тільки файли менше 5 МБ (")

    elif file_name.split(".")[-1] != "pdf":
        bot.send_message(chat_id, text="Приймаю тільки файли формату pdf")

    else:
        if user.cv_file_id is not None:
            answer = "Дякую, я оновив твоє резюме!"
        else:
            answer = "Дякую, зберіг!"

        user.cv_file_id = file_id
        user.cv_file_name = file_name
        user.save()

        bot.send_message(chat_id, text=answer)

        print(f"{user.name} загрузив {file_name} розміром {file_size/(1024**2)} МБ")


def send_welcome_message_and_start_quiz(user: User):
    ejf = data.get_ejf()
    welcome_text = ejf.content.start_text
    welcome_photo = ejf.content.ejf_start_photo
    bot.send_photo(chat_id=user.chat_id, photo=welcome_photo, caption=welcome_text)

    final_func = user_section.send_start_menu

    # if Job Fair not ended
    # if user.last_interaction_date < data.JOB_FAIR_END_TIME:
    #    final_func = job_fair_section.send_start_menu
    #
    ## if Job Fair ended
    # else:
    #    final_func = user_section.send_start_menu

    quiz.start_starting_quiz(user, bot, final_func)


if __name__ == "__main__":
    updater.start_update_threads()

    bot.polling(none_stop=True)

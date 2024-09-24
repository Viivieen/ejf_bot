from telebot.types import Message, KeyboardButton, CallbackQuery
from telebot import TeleBot

from typing import Callable

from src.data import User, JobFair, Data


help_msg = (
    "TEST COMMANDS HELP\n\n"
    "<b>ejf__help</b> - for help message\n"
    "<b>ejf__update</b> - for updating content from Database\n"
    "<b>ejf__resetquiz</b> - full start of bot (with start message and quiz)\n"
    "<b>ejf__user</b> - user start menu\n"
    "<b>ejf__test_blocked</b> - test blocked users\n"
)


def process_tests_text(
    bot: TeleBot, user: User, data: Data, text: str, user_func: Callable
):
    test_action = text.split("__")[1]

    if test_action == "help":
        bot.send_message(user.chat_id, help_msg)

    elif test_action.startswith("edit"):
        btn_number = int(text.split("-")[-1])

    elif test_action == "update":
        data.update_ejf_table()
        bot.send_message(user.chat_id, text="EJF table has been updated")

    elif test_action == "resetquiz":
        user.additional_info = None
        user.save()
        bot.send_message(
            user.chat_id, text="You can now click /start and take a quiz again."
        )

    elif test_action == "user":
        user_func(user)

    elif test_action == "test_blocked":

        blocked_counter = 0
        unblocked_counter = 0
        for u in User.objects:
            try:
                m = bot.send_message(chat_id=u.chat_id, text="check")
                bot.delete_message(chat_id=u.chat_id, message_id=m.message_id)
                if u.is_blocked:
                    u.is_blocked = False
                    bot.send_message(
                        user.chat_id, text=f"{u.chat_id} @{u.username} unblocked!!!!"
                    )
                    u.save()
                    unblocked_counter += 1

            except Exception as e:
                bot.send_message(user.chat_id, text=f"{u.chat_id} @{u.username} {e}")
                if u.is_blocked is False:
                    u.is_blocked = True
                    u.save()
                    blocked_counter += 1

        bot.send_message(
            user.chat_id,
            text=f"Заблоковано нових {blocked_counter}\nРозблоковано нових {unblocked_counter}",
        )

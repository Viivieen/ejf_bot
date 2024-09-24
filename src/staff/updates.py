from datetime import datetime, timezone
import threading
from time import sleep

from telebot.types import Message

from ..data import User, Company, Vacancy, JobFair
from src.staff import utils


class Updater:

    UPDATE_HOUR = 8  # 8:00 every morning
    DEFAULT_PROMOTE_COUNTER = 1

    def __init__(self):
        super().__init__()

    def start_update_threads(self):

        promote_thread = threading.Thread(target=self.promote_update_thread)
        promote_thread.start()

    def promote_update_thread(self):

        try:
            while True:
                current_hour = datetime.now().hour
                if current_hour != self.UPDATE_HOUR:
                    hours_left = (
                        self.UPDATE_HOUR - current_hour
                        if current_hour < self.UPDATE_HOUR
                        else 24 % current_hour + self.UPDATE_HOUR
                    )

                    print(f"Time left to promote update - {hours_left} hours")

                    seconds_left = current_hour * 60 * 60
                    sleep(seconds_left)

                print("Start updating companies promotions...")

                company_list = Company.objects.filter()
                for company in company_list:
                    company.promote_counter = self.DEFAULT_PROMOTE_COUNTER
                    company.save()

                print("Finished updating companies promotions...")

                sleep(24 * 60 * 60)
        except Exception as e:
            print(f"(Updater exception) Promote thread - {e}")
            promote_thread = threading.Thread(target=self.promote_update_thread)
            promote_thread.start()

    def update_user_interaction_time(self, message: Message) -> User:
        user_chat_id = message.chat.id
        date = utils.get_now()

        user = User.objects.filter(chat_id=user_chat_id)

        # add user if it does not exist
        if len(user) == 0:
            ejf = JobFair.objects.first()

            username = (
                message.chat.username
                if message.chat.username is not None
                else "No Nickname"
            )
            name = (
                message.chat.first_name
                if message.chat.first_name is not None
                else "No Name"
            )
            surname = (
                message.chat.last_name
                if message.chat.last_name is not None
                else "No Surname"
            )
            register_source = (
                message.text.split()[1] if len(message.text.split()) > 1 else "Unknown"
            )

            user = User(
                chat_id=user_chat_id,
                name=name,
                surname=surname,
                username=username,
                interests=ejf.filters_interest,
                experience=ejf.filters_experience,
                employment=ejf.filters_employment,
                register_source=register_source,
                registration_date=date,
                last_update_date=date,
                last_interaction_date=date,
            )

            user.save()

        # update user if exists
        else:
            user = user[0]
            date = utils.get_now()
            user.update(last_interaction_date=date)

        return user

from telebot.types import (
    CallbackQuery,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from ..data import Data, User, JobFair, Vacancy, VacancyApplyLog
from ..objects import quiz, vacancy as vacancy_module, interests
from .section import Section
from ..staff import utils
from random import randint


class UserSection(Section):
    TEXT_BUTTONS = ["Найти вакансію", "Хто ми?", "Профіль"]

    def __init__(self, data: Data):
        super().__init__(data=data)

    def process_callback(self, call: CallbackQuery, user: User):
        action = call.data.split(";")[1]

        # check if user is not HR
        if user.hr_status is True:
            self.bot.answer_callback_query(call.id, text="HR не має доступу сюди :(")
            return

        if action == "ApplyVacancy":
            vacancy_id = call.data.split(";")[3]
            self.apply_for_vacancy(user, vacancy_id, call=call)

        elif action == "VacInfo":
            self.send_vacancy_info(user, call=call)

        elif action == "Profile":
            self.send_profile_menu(user, call)

        elif action == "Interests":
            self.send_filters_menu(call, user, interest=True)

        elif action == "Experience":
            self.send_filters_menu(call, user, experience=True)

        elif action == "Employment":
            self.send_filters_menu(call, user, employment=True)

        elif action == "CV":
            self.send_cv_request(call, user)

        else:
            self.answer_wrong_action(call)

        self.bot.answer_callback_query(call.id)

    def process_text(self, text: str, user: User):

        # check if user is not HR
        if user.hr_status is True:
            self.bot.send_message(user.chat_id, text="HR не має доступу сюди :(")
            return

        if text == self.TEXT_BUTTONS[0]:
            self.send_vacancy_info(user, is_random=True)

        elif text == self.TEXT_BUTTONS[1]:
            self.send_about_info(user)

        elif text == self.TEXT_BUTTONS[2]:
            self.send_profile_menu(user)

    def send_start_menu(self, user: User):
        ejf = self.data.get_ejf()

        btn_vacancy = KeyboardButton(text=self.TEXT_BUTTONS[0])
        # btn_who = KeyboardButton(text=self.TEXT_BUTTONS[1])
        btn_profile = KeyboardButton(text=self.TEXT_BUTTONS[2])

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(btn_vacancy)
        markup.add(btn_profile)

        self.bot.send_photo(
            user.chat_id,
            caption=ejf.content.user_start_text,
            photo=ejf.content.user_start_photo,
            reply_markup=markup,
        )

    def send_profile_menu(self, user: User, call: CallbackQuery = None):
        text_message = """

        """
        text_message += self._form_profile_vacancy_count_text(user)

        markup = self._form_profile_menu_markup()

        if call is None:
            self.bot.send_message(
                chat_id=user.chat_id, text=text_message, reply_markup=markup
            )
        else:
            self.send_message(call, text=text_message, reply_markup=markup)

    def send_filters_menu(
        self,
        call: CallbackQuery,
        user: User,
        interest=False,
        experience=False,
        employment=False,
    ):
        text = str()
        markup = InlineKeyboardMarkup()

        ejf = JobFair.objects.first()

        if interest:
            interests.update_user(call, user.interests, ejf.filters_interest)
            markup = interests.create_interests_markup(user)

        elif experience:
            interests.update_user(call, user.experience, ejf.filters_experience)
            markup = interests.create_experience_markup(user)

        elif employment:
            interests.update_user(call, user.employment, ejf.filters_employment)
            markup = interests.create_employment_markup(user)

        # Back button
        back_btn_callback = self.form_user_callback(action="Profile", edit=True)
        back_btn = self.create_back_button(back_btn_callback)
        markup.add(back_btn)

        text += self._form_profile_vacancy_count_text(user=user)

        self.send_message(call, text=text, reply_markup=markup)

        user.save()

    def send_about_info(self, user: User):
        self.bot.send_message(user.chat_id, text="Test")

    def apply_for_vacancy(
        self, user: User, vacancy_id: str, call: CallbackQuery = None
    ):
        vacancy = Vacancy.objects.with_id(vacancy_id)
        hr = vacancy.company.HR

        # if there is no hr
        if hr is None:
            print(
                f"{vacancy.company.name} не має HR при подачі на вакансію {vacancy.name}"
            )
            self.bot.send_message(
                user.chat_id,
                text="Ой, ця вакансія не робоча :(\nСпробуй знайти іншу, а цю я поки приберу.",
            )
            return

        # check if user has CV
        if user.cv_file_id is None:
            answer_no_cv = "Потрібно добавити своє резюме!"
            self.bot.send_message(user.chat_id, text=answer_no_cv)
            return

        # check if user hasn't applied for vacancy yet
        user_prev_apply = VacancyApplyLog.objects.filter(
            user=user, vacancy=vacancy
        ).first()
        if user_prev_apply is not None:
            answer_double_apply = "Ти вже подавався сюди!"
            self.bot.send_message(user.chat_id, text=answer_double_apply)
            return

        # TODO ? check apply_count of user

        # save info about apply to DB
        new_user_apply = VacancyApplyLog(
            vacancy=vacancy, user=user, apply_datetime=utils.get_now()
        )
        new_user_apply.save(force_insert=True)

        # Send info about apply to user
        message_to_user = (
            f"Твоє резюме надіслано менеджеру {vacancy.company.name}!\n"
            # f"Щоб переглянути свої подачі, натискай команду /vacancy_applies"
        )
        self.bot.send_message(user.chat_id, text=message_to_user)

        # Send info about apply to HR
        message_to_hr = f"Нова подача на вакансію <b>{vacancy.name}</b>"
        info_btn_name = "Переглянути"
        info_btn_callback = self.form_hr_callback(
            action="ApplyInfo", vacancy_id=vacancy_id, edit=True
        )
        apply_info_markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton(text=info_btn_name, callback_data=info_btn_callback)
        )
        self.bot.send_message(
            hr.chat_id, text=message_to_hr, reply_markup=apply_info_markup
        )

    def send_vacancy_info(
        self,
        user: User,
        is_random: bool = False,
        spec_vacancy: Vacancy = None,
        call: CallbackQuery = None,
    ):
        # get vacancies list by user's filters
        vacancies = self._get_vacancy_list_by_filters(user=user)

        # check if any vacancies exist
        if vacancies.count() == 0 and spec_vacancy is None:
            self.bot.send_message(
                user.chat_id,
                text="За вибраними критеріями не знайдено жодної вакансії :(\nПереходь в меню 'Профіль'",
            )
            return

        # get current vacancy and it's index in all vacancy list
        if is_random:
            vac_index = randint(0, vacancies.count() - 1)
            vac = vacancies[vac_index]
        elif spec_vacancy:
            vac = spec_vacancy
            vac_index = 0 if vacancies.count() == 0 else list(vacancies).index(vac)
        else:
            vacancy_id = call.data.split(";")[3]
            vac = Vacancy.objects.with_id(vacancy_id)
            vac_index = list(vacancies).index(vac)

        # form content of vacancy to be send to user
        vacancy_description = vacancy_module.form_vacancy_info(
            vacancy=vac, status=False
        )
        company_photo = vac.company.photo_id
        vacancy_info_menu_markup = self._form_vacancy_info_menu_markup(
            user=user, vacancy=vac, vacancies=list(vacancies), cur_vac_index=vac_index
        )

        # send vacancy info
        if call:
            self.send_message(
                call, vacancy_description, company_photo, vacancy_info_menu_markup
            )
        else:
            self.bot.send_photo(
                chat_id=user.chat_id,
                photo=company_photo,
                caption=vacancy_description,
                reply_markup=vacancy_info_menu_markup,
            )

    def send_cv_request(self, call: CallbackQuery, user: User):
        text = "Надсилай сюди резюме — PDF не більше 5МБ."
        photo = "https://i.ibb.co/x7mxtk5/bot-06.png"

        self.send_message(call, text=text, photo=photo)

    def _get_vacancy_list_by_filters(self, user: User):
        return Vacancy.objects.filter(
            tag__in=user.interests,
            experience__in=user.experience,
            employment_type__in=user.employment,
            is_active=True,
        )

    def _form_vacancy_info_menu_markup(
        self, user: User, vacancy: Vacancy, vacancies: list, cur_vac_index: int
    ) -> InlineKeyboardMarkup:

        vacancy_menu_markup = InlineKeyboardMarkup()

        # full info
        full_info_btn = vacancy_module.create_vacancy_telegraph_page_button(vacancy)
        vacancy_menu_markup.add(full_info_btn)

        # company info
        company_info_btn = InlineKeyboardButton(
            text="Про компанію", url=vacancy.company.company_url
        )
        vacancy_menu_markup.add(company_info_btn)

        # apply with CV button
        btn_text = "Податися за допомогою CV"
        btn_callback = self.form_user_callback(
            action="ApplyVacancy", vacancy_id=vacancy.id, edit=True
        )
        btn_cv = InlineKeyboardButton(text=btn_text, callback_data=btn_callback)
        vacancy_menu_markup.add(btn_cv)

        # left right
        next_vac_index = int()

        if cur_vac_index == len(vacancies) - 1:
            next_vac_index = 0
        else:
            next_vac_index = cur_vac_index + 1

        prev_vac_index = cur_vac_index - 1

        if len(vacancies) != 0:
            prev_vac = vacancies[prev_vac_index]
            next_vac = vacancies[next_vac_index]
        else:
            prev_vac = vacancy
            next_vac = vacancy

        # previous vacancy button
        btn_text = "👈"
        btn_callback = self.form_user_callback(
            action="VacInfo", vacancy_id=prev_vac.id, edit=True
        )
        btn_prev = InlineKeyboardButton(text=btn_text, callback_data=btn_callback)

        # counter button
        btn_text = f"{cur_vac_index+1}/{len(vacancies)}"
        btn_counter = InlineKeyboardButton(btn_text, callback_data="IGNORE")

        # next vacancy button
        btn_text = "👉"
        btn_callback = self.form_user_callback(
            action="VacInfo", vacancy_id=next_vac.id, edit=True
        )
        btn_next = InlineKeyboardButton(text=btn_text, callback_data=btn_callback)

        vacancy_menu_markup.add(btn_prev, btn_counter, btn_next)

        return vacancy_menu_markup

    def _form_profile_vacancy_count_text(self, user: User) -> str:

        vacancies = self._get_vacancy_list_by_filters(user)

        return (
            f"\nЗа вибраними критеріями знайдено вакансій - <b>{vacancies.count()}</b>"
        )

    def _form_profile_menu_markup(self) -> InlineKeyboardMarkup:
        criteria_markup = InlineKeyboardMarkup()

        # Interests button
        interest_but = InlineKeyboardButton(
            text="Інтереси",
            callback_data=self.form_user_callback(action="Interests", edit=True),
        )

        # Experience button
        experience_but = InlineKeyboardButton(
            text="Досвід",
            callback_data=self.form_user_callback(action="Experience", edit=True),
        )

        # Employment type button
        employ_but = InlineKeyboardButton(
            text="Зайнятість",
            callback_data=self.form_user_callback(action="Employment", edit=True),
        )

        # CV button
        cv_but = InlineKeyboardButton(
            text="Резюме",
            callback_data=self.form_user_callback(action="CV", new=True),
        )

        criteria_markup.add(interest_but)
        criteria_markup.add(experience_but)
        criteria_markup.add(employ_but)
        criteria_markup.add(cv_but)

        return criteria_markup

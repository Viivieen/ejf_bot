from telebot.types import CallbackQuery

from ..data import Data, User, Company, Vacancy, VacancyApplyLog
from .section import Section
from .user import UserSection  ###### bad thing
from ..objects import vacancy as vacancy_module, quiz
from ..staff import utils
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)


class HRSection(Section):
    def __init__(self, data: Data):
        super().__init__(data=data)

    def process_callback(self, call: CallbackQuery, user: User):
        action = call.data.split(";")[1]

        # check if user is HR
        if user.hr_status is False:
            self.bot.answer_callback_query(call.id, text="Ти наразі не HR :(")
            return

        if action == "StartMenu":
            self.send_start_menu(user, call)

        elif action == "VacancyList":
            self.send_vacancy_list(user, call)

        elif action == "AddVacancy":
            self.add_new_vacancy(user)

        elif action == "VacInfo":
            self.send_vacancy_info(user, call)

        elif action == "DeleteVacancy":
            self.delete_vacancy(user, call)

        elif action == "ChangeVacancyStatus":
            self.change_vacancy_status(user, call)

        elif action == "VacancyStatistics":
            self.send_vacancy_statistics(user, call)

        elif action == "VacancyEditMenu":
            self.send_edit_vacancy_menu(user, call)

        elif action == "VacancyPromote":
            self.promote_vacancy(user, call)

        elif action.startswith("VacChange"):
            self.change_vacancy_info(user, call)

        elif action == "CompanyInfo":
            pass

        elif action == "QuitHR":
            self.exit_hr(user, call)

        elif action == "ApplyInfo":
            self.send_vacancy_apply_info(user, call)

        elif action == "ApplyList":
            self.answer_in_development(call)

        elif action == "GetCV":
            self.send_user_cv(user, call)

        else:
            pass

        self.bot.answer_callback_query(call.id)

    def process_text(self, text):
        pass

    def register_hr(self, user: User, login_str: str):
        company_key = login_str.split("_")[-1]

        company = Company.objects.filter(token=company_key).first()

        # check if company with such key exists
        if company is None:
            self.bot.send_message(
                user.chat_id, text="Компанії з таким ключем не існує :("
            )
            return

        # check if there is no HR in company
        if company.HR is not None:
            if company.HR.chat_id != user.chat_id:
                self.bot.send_message(
                    user.chat_id,
                    text=f"Упс!\nЗа компанією {company.name} вже закріплений користувач {user.name} @{user.username}",
                )
            else:
                self.send_start_menu(user)
            return

        # check if user is not HR yet
        if user.hr_status:
            self.bot.send_message(
                user.chat_id,
                text=f"Упс!\nТи вже належиш до іншої компанії :)",
            )
            return

        # connect hr to company is everything is all right
        company.HR = user
        company.save()

        user.hr_status = True
        user.save()

        # remove user keyboard
        del_message = self.bot.send_message(
            user.chat_id, text="Login suceeded", reply_markup=ReplyKeyboardRemove()
        )
        self.bot.delete_message(user.chat_id, del_message.message_id)

        self.send_start_menu(user)

    def send_start_menu(self, user: User, call: CallbackQuery = None):
        company = Company.objects.filter(HR=user).first()

        text = ""
        photo = company.photo_id
        start_markup = self._form_start_markup(user)

        if call is None:
            self.bot.send_photo(
                chat_id=user.chat_id,
                caption=text,
                photo=photo,
                reply_markup=start_markup,
            )
        else:
            self.send_message(call, text=text, photo=photo, reply_markup=start_markup)

    def send_vacancy_list(self, user: User, call: CallbackQuery = None):
        company = Company.objects.filter(HR=user).first()

        vac_text = "Список ваших вакансій"
        company_photo = company.photo_id
        vac_list_markup = self._form_vac_list_markup(user, company)

        if call is None:
            self.bot.send_photo(
                chat_id=user.chat_id,
                caption=vac_text,
                photo=company_photo,
                reply_markup=vac_list_markup,
            )
        else:
            self.send_message(
                call, vac_text, photo=company_photo, reply_markup=vac_list_markup
            )

    def send_vacancy_info(self, user: User, call: CallbackQuery = None):
        vacancy_id = call.data.split(";")[4]
        vacancy = Vacancy.objects.with_id(vacancy_id)

        company_photo = vacancy.company.photo_id

        vacancy_description = self._form_vacancy_info(vacancy=vacancy)
        markup = self._form_vacancy_menu_markup(vacancy)

        self.send_message(
            call, photo=company_photo, text=vacancy_description, reply_markup=markup
        )

    def delete_vacancy(self, user: User, call: CallbackQuery):
        vacancy_id = call.data.split(";")[4]
        vacancy = Vacancy.objects.with_id(vacancy_id)

        result = vacancy_module.delete_vacancy(vacancy)

        # change call callback data to send previous menu
        call.data = self.form_hr_callback(action="VacancyList", edit=True)

        self.bot.answer_callback_query(call.id, text=result)

        self.send_vacancy_list(user, call)

    def change_vacancy_status(self, user: User, call: CallbackQuery):
        vacancy_id = call.data.split(";")[4]

        vacancy = Vacancy.objects.with_id(vacancy_id)
        vacancy_module.change_vacancy_status(vacancy)

        self.send_vacancy_info(user, call)

    def send_vacancy_statistics(self, user: User, call: CallbackQuery):
        self.answer_in_development(call)

    def send_edit_vacancy_menu(self, user: User, call: CallbackQuery):
        vacancy_id = call.data.split(";")[4]
        vacancy = Vacancy.objects.with_id(vacancy_id)

        text = (
            f"{self._form_vacancy_info(vacancy)}\n"
            "Вибирай поле, яке потрібно відредагувати:"
        )
        photo = vacancy.company.photo_id
        markup = self._form_vacancy_edit_menu_markup(vacancy=vacancy)

        self.send_message(call, text, photo, markup)

    def change_vacancy_info(self, user: User, call: CallbackQuery):
        action = call.data.split(";")[1]
        vacancy_id = call.data.split(";")[4]
        vacancy = Vacancy.objects.with_id(vacancy_id)

        field_to_change = action.split("-")[1]

        vacancy_module.change_vacancy_info(
            field=field_to_change,
            vacancy_name=vacancy.name,
            user=user,
            bot=self.bot,
            next_step=None,
            telegraph_account=self.data.telegraph,
        )

    def send_vacancy_apply_info(self, user: User, call: CallbackQuery):
        vacancy_id = call.data.split(";")[4]

        # get objects from db
        vacancy = Vacancy.objects.with_id(vacancy_id)
        vacancy_apply_log = VacancyApplyLog.objects.filter(vacancy=vacancy).first()

        # update apply vacancy apply log
        vacancy_apply_log.last_view_datetime = utils.get_now()
        vacancy_apply_log.view_count += 1

        # form text
        apply_datetime = vacancy_apply_log.apply_datetime.strftime("%m/%d/%Y, %H:%M")
        apply_info = (
            f"<b>{vacancy.name}</b>\n\n"
            f"<b>Нікнейм в телеграмі</b> - @{vacancy_apply_log.user.username}\n\n"
            f"<b>Дата подачі</b> - {apply_datetime}"
        )

        # form markup
        markup = self._form_vac_apply_info_markup(vacancy_apply_log.user)

        self.send_message(call, text=apply_info, reply_markup=markup)

    def send_user_cv(self, user: User, call: CallbackQuery):
        applied_user_id = call.data.split(";")[2]
        applied_user = User.objects.with_id(applied_user_id)
        cv_file_id = applied_user.cv_file_id

        self.bot.send_document(user.chat_id, data=cv_file_id)

    def add_new_vacancy(self, user: User):
        vacancy_module.start_add_vacancy_quiz(
            user,
            bot=self.bot,
            next_step=self.send_vacancy_list,
            telegraph_account=self.data.telegraph,
        )

    def exit_hr(self, user: User, call: CallbackQuery):
        company = Company.objects.filter(HR=user).first()

        company.HR = None
        company.save()

        user.hr_status = False
        user.save()

        text = f"Ти успішно вийшов з компанії {company.name}!\n"
        self.send_message(call, text=text)

    def promote_vacancy(self, user: User, call: CallbackQuery):

        # check promote limit
        company = Company.objects.filter(HR=user).first()
        if company.promote_counter == 0:
            self.send_message(
                call, text="Можна здійснювати лише один промоут вакансії в день."
            )
            return

        # update company promote counter
        company.promote_counter -= 1
        company.save()

        # get target users list
        vacancy_id = call.data.split(";")[4]
        vacancy = Vacancy.objects.with_id(vacancy_id)
        target_users = User.objects.filter(is_blocked=False, hr_status=False)

        # send info about sending
        self.bot.send_message(
            user.chat_id,
            text="Розпочинаю процес розповсюдження вакансії...\nЦе може зайняти декілька хвилин😉",
        )

        # send vacancy to target users
        temp_user_section = UserSection(data=self.data)
        receivers_count = 0
        for target_user in target_users:
            if vacancy.tag not in list(target_user.interests):
                continue

            try:
                temp_user_section.send_vacancy_info(
                    user=target_user, spec_vacancy=vacancy
                )
            except Exception as e:
                print(f"(Promoting exception) {user.username} {vacancy.name} - {e}")
                target_user.is_blocked = True
                target_user.save()
                continue

            receivers_count += 1

        # final message
        if receivers_count != 0:
            self.bot.send_message(
                user.chat_id,
                text=f"Вакансію отримало {receivers_count} користувачів!\n",
            )
        else:
            self.bot.send_message(
                user.chat_id, text=f"Нажаль, в мене нічого не вийшло😞"
            )
            company.promote_counter += 1
            company.save()

    def _form_start_markup(self, user: User) -> InlineKeyboardMarkup:
        start_markup = InlineKeyboardMarkup()

        # company info
        company = Company.objects.filter(HR=user).first()
        company_info_btn = InlineKeyboardButton(
            text="Про компанію", url=company.company_url
        )
        start_markup.add(company_info_btn)

        # my vacancies
        btn_text1 = "Мої вакансії"
        btn_callback_vaclist = self.form_hr_callback(action="VacancyList", edit=True)
        btn_my_vacancies = InlineKeyboardButton(
            btn_text1, callback_data=btn_callback_vaclist
        )
        start_markup.add(btn_my_vacancies)

        # my company
        btn_text2 = "Моя компанія"
        btn_callback_company = self.form_hr_callback(action="CompanyInfo", edit=True)
        btn_my_company = InlineKeyboardButton(
            btn_text2, callback_data=btn_callback_company
        )
        # start_markup.add(btn_my_company)

        # quit hr
        btn_text3 = "Вийти з профілю компанії"
        btn_callback_sign_out = self.form_hr_callback(action="QuitHR", delete=True)
        btn_sign_out_from_company = InlineKeyboardButton(
            btn_text3, callback_data=btn_callback_sign_out
        )
        start_markup.add(btn_sign_out_from_company)

        return start_markup

    def _form_vac_list_markup(
        self, user: User, company: Company
    ) -> InlineKeyboardMarkup:
        vac_list_markup = InlineKeyboardMarkup()

        vacancy_list = Vacancy.objects.filter(company=company)

        # Every vacancy list
        for vacancy in vacancy_list:
            button_text = vacancy.name
            callback = self.form_hr_callback(
                action="VacInfo", vacancy_id=vacancy.id, edit=True
            )
            vacancy_button = InlineKeyboardButton(button_text, callback_data=callback)
            vac_list_markup.add(vacancy_button)

        # Add new vacancy btn
        btn_text = "Додати нову"
        btn_callback = self.form_hr_callback(action="AddVacancy", edit=True)
        btn_new_vacancy = InlineKeyboardButton(btn_text, callback_data=btn_callback)

        # Back button
        btn_callback = self.form_hr_callback(action="StartMenu", edit=True)
        btn_back = self.create_back_button(btn_callback)

        vac_list_markup.add(btn_back, btn_new_vacancy)

        return vac_list_markup

    def _form_vacancy_menu_markup(self, vacancy: Vacancy) -> InlineKeyboardMarkup:

        vacancy_menu_markup = InlineKeyboardMarkup()

        company_id = vacancy.company.id

        # full info
        full_info_btn = vacancy_module.create_vacancy_telegraph_page_button(vacancy)
        vacancy_menu_markup.add(full_info_btn)

        # delete vacancy
        btn_text = "Видалити вакансію"
        btn_callback = self.form_hr_callback(
            action="DeleteVacancy",
            vacancy_id=vacancy.id,
            delete=True,
        )
        delete_vacancy_btn = InlineKeyboardButton(
            text=btn_text, callback_data=btn_callback
        )
        vacancy_menu_markup.add(delete_vacancy_btn)

        # on\off
        if vacancy.is_active:
            btn_text = "Дезактивувати"
        else:
            btn_text = "Активувати"
        btn_callback = self.form_hr_callback(
            action="ChangeVacancyStatus", vacancy_id=vacancy.id, edit=True
        )
        change_state_btn = InlineKeyboardButton(
            text=btn_text, callback_data=btn_callback
        )
        vacancy_menu_markup.add(change_state_btn)

        # statistics
        btn_text = "Статистика"
        btn_callback = self.form_hr_callback(
            action="VacancyStatistics", vacancy_id=vacancy.id, edit=True
        )
        vacancy_statistics_btn = InlineKeyboardButton(
            text=btn_text, callback_data=btn_callback
        )
        # vacancy_menu_markup.add(vacancy_statistics_btn)

        # edit vacancy menu
        btn_text = "Редагувати вакансію"
        btn_callback = self.form_hr_callback(
            action="VacancyEditMenu", vacancy_id=vacancy.id, edit=True
        )
        edit_vacancy_menu_btn = InlineKeyboardButton(
            text=btn_text, callback_data=btn_callback
        )
        vacancy_menu_markup.add(edit_vacancy_menu_btn)

        # promote vacancy
        btn_text = "Розіслати вакансію 🎯"
        btn_callback = self.form_hr_callback(
            action="VacancyPromote", vacancy_id=vacancy.id, new=True
        )
        promote_vacancy_btn = InlineKeyboardButton(
            text=btn_text, callback_data=btn_callback
        )
        vacancy_menu_markup.add(promote_vacancy_btn)

        # back button
        company = vacancy.company
        btn_callback = self.form_hr_callback(
            action="VacancyList", company_id=company.id, edit=True
        )
        btn_back = self.create_back_button(btn_callback)
        vacancy_menu_markup.add(btn_back)

        return vacancy_menu_markup

    def _form_vacancy_info(self, vacancy: Vacancy) -> str:
        vacancy_description = (
            f"<b>{vacancy.name}</b>\n\n"
            f"<b>Категорія</b>: {vacancy.tag}\n"
            f"<b>Досвід</b>: {vacancy.experience}\n"
            f"<b>Зарплата</b>: {vacancy.salary}\n"
            f"<b>Робочий день</b>: {vacancy.employment_type}\n"
            # f"<b>Опис</b>: \n{vacancy.description}\n"
        )

        if vacancy.is_active:
            is_active = "Активовано"
            # vacancy_description += f"<b>Вакансія дезактивується через: </b>: {vacancy.active_days_left} днів\n"
        else:
            is_active = "Дезактивовано"

        add_date = vacancy.add_date.strftime("%d/%m/%Y, %H:%M")

        vacancy_description += (
            f"<b>Статус</b>: {is_active}\n"
            f"<b>Додано</b>: {add_date}\n"
            # f"<b>Оновлено</b>: {vacancy.last_update_date}\n"
        )

        return vacancy_description

    def _form_vacancy_edit_menu_markup(self, vacancy: Vacancy) -> InlineKeyboardMarkup:

        vacancy_edit_menu_markup = InlineKeyboardMarkup()

        editable_field_info = Vacancy.get_editable_field_info()

        # field buttons
        for edit_field, btn_name in editable_field_info.items():
            action = f"VacChange-{edit_field}"
            btn_callback = self.form_hr_callback(
                action, vacancy_id=vacancy.id, edit=True
            )
            btn = InlineKeyboardButton(btn_name, callback_data=btn_callback)
            vacancy_edit_menu_markup.add(btn)

        # back button
        back_btn_callback = self.form_hr_callback(
            action="VacInfo", vacancy_id=vacancy.id, edit=True
        )
        back_btn = self.create_back_button(back_btn_callback)
        vacancy_edit_menu_markup.add(back_btn)

        return vacancy_edit_menu_markup

    def _form_vac_apply_info_markup(self, applied_user) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()

        # get CV btn
        btn_text = "Отримати резюме"
        btn_callback = self.form_hr_callback(
            action="GetCV", user_id=applied_user.id, new=True
        )
        btn = InlineKeyboardButton(btn_text, callback_data=btn_callback)
        markup.add(btn)

        # back to applies list
        btn_text = "Список подач"
        btn_callback = self.form_hr_callback(action="ApplyList", edit=True)
        btn = InlineKeyboardButton(btn_text, callback_data=btn_callback)
        markup.add(btn)

        return markup
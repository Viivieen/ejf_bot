from typing import Iterator
from ..data import User, Vacancy, Quiz, Company, Data
from ..objects import quiz
from ..staff import utils

from typing import Callable
from datetime import datetime, timezone
from telebot import TeleBot
from telebot.types import InlineKeyboardButton
from telegraph import Telegraph


def start_add_vacancy_quiz(
    user: User, bot: TeleBot, next_step: Callable, telegraph_account: Telegraph
):
    vacancy_quiz = Quiz.objects.filter(name="VacancyQuiz").first()
    vacancy_quiz_questions = vacancy_quiz.questions

    quiz_iterator = iter(vacancy_quiz_questions)
    question = next(quiz_iterator)

    quiz.send_question(
        user,
        bot,
        question,
        quiz_iterator,
        save_func=_save_vacancy,
        final_func=next_step,
        container={"telegraph": telegraph_account},
        is_required=vacancy_quiz.is_required,
    )


def change_vacancy_info(
    field: str,
    vacancy_name: str,
    user: User,
    bot: TeleBot,
    next_step: Callable,
    telegraph_account: Telegraph,
):
    vacancy_quiz = Quiz.objects.filter(name="VacancyEditQuiz").first()

    # find right question in quiz
    for question in vacancy_quiz.questions:
        if question.name == field:
            vacancy_quiz_question = [question]
            break

    quiz_iterator = iter(vacancy_quiz_question)
    question = next(quiz_iterator)

    quiz.send_question(
        user,
        bot,
        question,
        quiz_iterator,
        save_func=_save_vacancy,
        final_func=next_step,
        container={"name": vacancy_name, "telegraph": telegraph_account},
        is_required=vacancy_quiz.is_required,
    )


def form_vacancy_info(vacancy: Vacancy, status: bool) -> str:

    vacancy_description = (
        f"{vacancy.name}\n"
        f"<b>Досвід</b>: {vacancy.experience}\n"
        f"<b>Зарплата</b>: {vacancy.salary}\n"
        f"<b>Робочий день</b>: {vacancy.employment_type}\n"
        # f"<b>Опис</b>: \n{vacancy.description}\n"
    )

    if status:
        if vacancy.is_active:
            is_active = "Активовано"
            vacancy_description += f"<b>Вакансія дезактивується через: </b>: {vacancy.active_days_left} днів\n"
        else:
            is_active = "Дезактивовано"

        vacancy_description += (
            f"<b>Статус</b>: {is_active}\n"
            f"<b>Додано</b>: {vacancy.add_date}\n"
            f"<b>Оновлено</b>: {vacancy.last_update_date}\n"
        )

    return vacancy_description


def create_vacancy_telegraph_page(vacancy: Vacancy, telegraph_account: Telegraph):
    title = vacancy.name

    parsed_description = vacancy.description.replace("\n", "<br>")

    html_content = (
        f"<b>Категорія</b>: {vacancy.tag}<br>"
        f"<b>Досвід</b>: {vacancy.experience}<br>"
        f"<b>Зарплата</b>: {vacancy.salary}<br>"
        f"<b>Робочий день</b>: {vacancy.employment_type}<br>"
        f"<h3>Опис</h3>{parsed_description}<br>"
    )

    author_name = telegraph_account.get_account_info()["author_name"]
    author_url = telegraph_account.get_account_info()["author_url"]

    try:
        response = telegraph_account.create_page(
            title=title,
            html_content=html_content,
            author_name=author_name,
            author_url=author_url,
        )

        vacancy.telegraph_link_token = response["path"]
        vacancy.save()
    except Exception as e:
        print(e)


def create_vacancy_telegraph_page_button(vacancy: Vacancy) -> InlineKeyboardButton:
    btn_text = "Детальніше"
    btn_url = (
        f"https://telegra.ph/{vacancy.telegraph_link_token}"
        if vacancy.telegraph_link_token
        else None
    )
    btn = InlineKeyboardButton(text=btn_text, url=btn_url, callback_data="IGNORE")

    return btn


def delete_vacancy(vacancy: Vacancy) -> str:
    vacancy_company = vacancy.company

    try:
        vacancy.delete()
        result = "Вакансію успішно видалено!"
        vacancy_company.vacancy_counter -= 1
    except:
        result = "Щось пішло не так :("

    return result


def change_vacancy_status(vacancy: Vacancy):
    vacancy.is_active = False if vacancy.is_active else True
    vacancy.save()


def _save_vacancy(user: User, container: dict):
    company = Company.objects.filter(HR=user).first()
    vacancy = Vacancy.objects.filter(company=company, name=container["name"]).first()

    if vacancy is None:
        vacancy = Vacancy()
        vacancy.company = company

        date = utils.get_now()
        vacancy.add_date = date
        vacancy.last_update_date = date

    if "name" in container:
        vacancy.name = container["name"]

    if "tag" in container:
        vacancy.tag = container["tag"]

    if "salary" in container:
        vacancy.salary = container["salary"]

    if "experience" in container:
        vacancy.experience = container["experience"]

    if "employment_type" in container:
        vacancy.employment_type = container["employment_type"]

    if "description" in container:
        vacancy.description = container["description"]

    if "telegraph" in container:
        create_vacancy_telegraph_page(vacancy, container["telegraph"])

    vacancy.save()
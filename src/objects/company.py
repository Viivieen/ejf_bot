from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from telebot.util import generate_random_token
from telebot import TeleBot

from typing import Callable

from ..data import Company, User, Vacancy, Quiz
from ..sections.section import Section
from ..staff import utils
from ..objects import quiz


def start_add_company_quiz(user: User, bot: TeleBot, next_step: Callable):
    company_quiz = Quiz.objects.filter(name="CompanyQuiz").first()
    company_quiz_questions = company_quiz.questions

    quiz_iterator = iter(company_quiz_questions)
    question = next(quiz_iterator)

    quiz.send_question(
        user,
        bot,
        question,
        quiz_iterator,
        save_func=_save_company,
        final_func=next_step,
        container={},
        is_required=company_quiz.is_required,
    )


def form_company_list_markup():
    # TODO import methos here
    pass


def form_company_description(call) -> tuple:
    company_id = call.data.split(";")[3]
    company = Company.objects.with_id(company_id)

    company_photo = company.photo_id
    company_description = (
        f"<b>Назва: </b> {company.name}\n"
        f"<b>Про компанію: </b> {company.description}\n"
    )
    # TODO add HR field

    return company_id, company_photo, company_description


def _save_company(user: User, container: dict):
    company = Company.objects.filter(HR=user).first()

    if company is None:
        company = Company()

        company.registration_date = utils.get_now()
        company.token = generate_random_token()

    if "name" in container:
        company.name = container["name"]

    if "photo_id" in container:
        company.photo_id = container["photo_id"]

    if "description" in container:
        company.description = container["description"]

    if "company_url" in container:
        company.company_url = container["company_url"]

    company.save()
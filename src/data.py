from telebot import TeleBot
from telegraph import Telegraph
import mongoengine as me
from datetime import datetime, timezone
import certifi

import string
import random


class Data:

    TEST_PHOTO = "https://i.ibb.co/0Gv4JyW/photo-2021-04-16-12-48-15.jpg"

    JOB_FAIR_END_TIME = datetime(2021, 5, 20, 20, 0, 0)

    def __init__(self, conn_string: str, bot: TeleBot):
        self.bot = bot

        me.connect(host=conn_string, tlsCAFile=certifi.where(), connect=False)
        print("connection success ")

        # if there is no ejf table in DB - then create it
        if len(JobFair.objects) == 0:
            self.reinit_ejf_table()
            print("ejf and content tables have been initialized")
        # if there was table already
        else:
            self.update_ejf_table()

        # create telegraph account
        self._create_telegraph_account()

        self.ADMIN_PASSWORD = self.get_ejf().admin_password

        # remove later
        # if there is no quiz table in DB - then create it
        self.add_quizes()

        # for user in User.objects:
        #    user.additional_info = None
        #    user.save()

    def add_test_company_with_vacancies(
        self, user, vacancies_number=2, photo=None, company_name=None
    ):

        # company
        name = self._generate_string() if company_name is None else company_name
        photo_id = self.TEST_PHOTO if photo is None else photo
        description = self._generate_string(long=True)
        vacancy_counter = 20  # ?
        HR = user
        token = self._generate_string()
        registration_date = datetime.now(tz=timezone.utc)

        test_company = Company(
            name=name,
            photo_id=photo_id,
            description=description,
            vacancy_counter=vacancy_counter,
            HR=HR,
            token=token,
            registration_date=registration_date,
        )
        test_company.save()

        # vacancies
        for i in range(vacancies_number):
            company = test_company
            name = self._generate_string()
            tag = self.get_ejf().filters_interest[
                random.randint(0, len(self.get_ejf().filters_interest) - 1)
            ]
            salary = f"{random.randint(1000, 5000)}$"
            experience = self.get_ejf().filters_experience[
                random.randint(0, len(self.get_ejf().filters_experience) - 1)
            ]
            employment_type = self.get_ejf().filters_employment[
                random.randint(0, len(self.get_ejf().filters_employment) - 1)
            ]
            description = self._generate_string(long=True)
            add_date = datetime.now(tz=timezone.utc)
            last_update_date = datetime.now(tz=timezone.utc)
            active_days_left = 14
            is_active = True

            vacancy = Vacancy(
                company=company,
                name=name,
                tag=tag,
                salary=salary,
                experience=experience,
                employment_type=employment_type,
                description=description,
                add_date=add_date,
                last_update_date=last_update_date,
                active_days_left=active_days_left,
                is_active=is_active,
            )

            from .objects import vacancy as vacancy_module

            vacancy_module.create_vacancy_telegraph_page(vacancy, self.telegraph)

            vacancy.save()

    def add_quizes(self):
        if len(Quiz.objects) == 0:
            self._add_start_quiz()
        # otherwise update it
        else:
            self.update_quiz_table()

        # add vacancy quiz
        if Quiz.objects.filter(name="VacancyQuiz").count() == 0:
            self._add_vacancy_quiz()
            print("Vacancy quiz has been added")

        # add vacancy quiz
        if Quiz.objects.filter(name="VacancyEditQuiz").count() == 0:
            self._add_vacancy_edit_quiz()
            print("Vacancy edit quiz has been added")

        # add company quiz
        if Quiz.objects.filter(name="CompanyQuiz").count() == 0:
            self._add_company_quiz()
            print("Company quiz has been added")

    def _add_start_quiz(self):

        quiz = Quiz(name="StartQuiz", is_required=True)

        q_name_surname = Question(
            name="name_surname",
            message="Як мені до тебе звертатися?",
            correct_answer_message="Гарно звучить 🥰",
            wrong_answer_message="Введи ім’я текстом 🤡",
        )

        q_age = Question(
            name="age",
            message="Скільки тобі років?",
            regex="[1-9][0-9]",
            correct_answer_message="Ого, ми однолітки 🥰",
            wrong_answer_message="Вкажи свій справжній вік 🤡",
        )

        q_school = Question(
            name="school",
            message="Де вчишся? Вибери або введи.",
            buttons=[
                "НУЛП",
                "ЛНУ",
                "УКУ",
                "КПІ",
                "КНУ",
                "Ще в школі",
                "Вже закінчив(-ла)",
            ],
            correct_answer_message="Клас 🥰",
            wrong_answer_message="Введи назву текстом 🤡",
        )

        q_study_term = Question(
            name="study_term",
            message="Який ти курс?",
            buttons=[
                "Перший",
                "Другий",
                "Третій",
                "Четвертий",
                "На магістартурі",
                "Нічого з переліченого",
            ],
            allow_user_input=False,
            correct_answer_message="Ідеальний час, щоб будувати кар'єру 🥰",
            wrong_answer_message="Вибери, будь ласка, один з варіантів 🤡",
        )

        ##############
        q_city = Question(
            name="city",
            message="Звідки ти? Вибери зі списку або введи назву.",
            buttons=["Львів", "Київ", "Новояворівськ", "Донецьк", "Стамбул"],
            correct_answer_message="Був-був там!",
            wrong_answer_message="Введи назву текстом :)",
        )

        q_contact = Question(
            name="contact",
            message="Обміняємося контактами?",
            buttons=["Тримай!"],
            input_type="contact",
            correct_answer_message="Дякую. А я залишаю тобі контакт головного організатора: @Slavkoooo 🥰",
            wrong_answer_message="Надішли, будь ласка, свій контакт 🤡",
        )

        q_email = Question(
            name="email",
            message="Наостанок, вкажи адресу своєї поштової скриньки.",
            regex="^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$",
            correct_answer_message="Дякую 🥰",
            wrong_answer_message="Введи, будь ласка, електронну адресу 🤡",
        )

        q_agree = Question(
            name="user_agreements",
            message="Залишилося тільки дати згоду на обробку даних.",
            buttons=["Я погоджуюсь."],
            allow_user_input=False,
        )

        q_register_end = Question(
            name="end_register",
            message="Хух, усі формальності позаду!\n\nЯ зареєстрував тебе на ІЯК. Далі нас очікують два дні пригод.\n\n<b>Поонлайнимо?</b> 🤓",
            buttons=[
                "Прийду подивитися 👀",
                "Прийду шукати роботу 🤑",
                "Прийду дізнатися щось нове 🧐",
                "Візьму участь у воркшопах✍️",
                "Все разом 🤹",
            ],
            allow_user_input=False,
        )

        quiz.questions = [
            q_name_surname,
            q_age,
            q_school,
            q_study_term,
            # q_city,
            q_contact,
            q_email,
            q_agree,
            q_register_end,
        ]

        quiz.save()

    def _add_vacancy_quiz(self):
        quiz = Quiz(name="VacancyQuiz", is_required=False)

        ejf = self.get_ejf()

        q_name = Question(
            name="name",
            message="Спочатку введи назву вакансії",
            max_text_size=100,
            correct_answer_message="Гарно звучить 🥰",
            wrong_answer_message="Введи назву текстом 🤡",
        )

        q_tag = Question(
            name="tag",
            message="Вибери категорію до якої відноситься вакансія",
            buttons=list(ejf.filters_interest),
            correct_answer_message="Ого, круто 🥰",
            wrong_answer_message="Не треба так робити",
            allow_user_input=False,
        )

        q_experience = Question(
            name="experience",
            message="Вибери наскільки досвідченим має бути твій новий працівник!",
            buttons=list(ejf.filters_experience),
            correct_answer_message="Ого, круто 🥰",
            wrong_answer_message="Не треба так робити",
            allow_user_input=False,
        )

        q_employment = Question(
            name="employment_type",
            message="Вибери тип зайнятості",
            buttons=list(ejf.filters_employment),
            correct_answer_message="Ого, круто 🥰",
            wrong_answer_message="Не треба так робити",
            allow_user_input=False,
        )

        q_salary = Question(
            name="salary",
            message="Введи скільки зароблятиме твій працівник",
            max_text_size=30,
            buttons=["Договірно"],
            correct_answer_message="Ого, круто 🥰",
            wrong_answer_message="Не треба так робити",
        )

        q_description = Question(
            name="description",
            message="Лишився останній штрих!\nНадішли мені стислий опис своєї вакансії, щоб кандидат міг зрозуміти, чим він буде займатись.\n\n<b>Максимум 2000 символів</b>",
            max_text_size=2000,
            correct_answer_message="Клас 🥰",
            wrong_answer_message="Введи опис текстом і не більше 2000 символів 🤡",
        )

        quiz.questions = [
            q_name,
            q_tag,
            q_experience,
            q_employment,
            q_salary,
            q_description,
        ]

        quiz.save()

    def _add_vacancy_edit_quiz(self):
        quiz = Quiz(name="VacancyEditQuiz", is_required=False)

        ejf = self.get_ejf()

        q_tag = Question(
            name="tag",
            message="Вибери категорію до якої відноситься вакансія",
            buttons=list(ejf.filters_interest),
            correct_answer_message="Ого, круто 🥰",
            wrong_answer_message="Не треба так робити",
            allow_user_input=False,
        )

        q_experience = Question(
            name="experience",
            message="Вибери наскільки досвідченим має бути твій новий працівник!",
            buttons=list(ejf.filters_experience),
            correct_answer_message="Ого, круто 🥰",
            wrong_answer_message="Не треба так робити",
            allow_user_input=False,
        )

        q_employment = Question(
            name="employment_type",
            message="Вибери тип зайнятості",
            buttons=list(ejf.filters_employment),
            correct_answer_message="Ого, круто 🥰",
            wrong_answer_message="Не треба так робити",
            allow_user_input=False,
        )

        q_salary = Question(
            name="salary",
            message="Введи скільки зароблятиме твій працівник",
            max_text_size=30,
            buttons=["Договірно"],
            correct_answer_message="Ого, круто 🥰",
            wrong_answer_message="Не треба так робити",
        )

        q_description = Question(
            name="description",
            message="Лишився останній штрих!\nНадішли мені стислий опис своєї вакансії, щоб кандидат міг зрозуміти, чим він буде займатись.\n\n<b>Максимум 2000 символів</b>",
            max_text_size=2000,
            correct_answer_message="Клас 🥰",
            wrong_answer_message="Введи опис текстом і не більше 2000 символів 🤡",
        )

        quiz.questions = [
            q_tag,
            q_experience,
            q_employment,
            q_salary,
            q_description,
        ]

        quiz.save()

    def _add_company_quiz(self):
        quiz = Quiz(name="CompanyQuiz", is_required=False)

        q_name = Question(
            name="name",
            message="Спочатку введи назву компанії",
            max_text_size=30,
            correct_answer_message="Гарно звучить 🥰",
            wrong_answer_message="Введи назву текстом 🤡",
        )

        q_photo_id = Question(
            name="photo_id",
            message="Скинь фотку компанії",
            input_type="photo",
            correct_answer_message="Ого, круто 🥰",
            wrong_answer_message="Не треба так робити",
        )

        q_description = Question(
            name="description",
            message="Надішли опис компанії",
            max_text_size=2000,
            correct_answer_message="Клас 🥰",
            wrong_answer_message="Введи опис текстом і не більше 2000 символів 🤡",
        )

        q_company_url = Question(
            name="company_url",
            message="Надішли посилання на сайт компанії",
            regex="^https:\/\/.*",
            correct_answer_message="Клас 🥰",
            wrong_answer_message="Введи посилання яке починається на <b>https://</b>",
        )

        quiz.questions = [q_name, q_photo_id, q_description, q_company_url]

        quiz.save()

    def reinit_ejf_table(self):
        # delete collections
        JobFair.objects.delete()
        Content.objects.delete()

        # create content table
        content = Content()
        content.start_text = (
            "Йоу, друзі! Теж помітили, що останнім часом зникли запахи і їжа якось не так смакує? 😔 Усе ясно: життя без ІЯКу втратило смак.\n\n"
            "🌤 Нам пощастило, що до 19 травня залишилося зовсім трохи. А що там 19 травня? А там <b>повернення легендарного Інженерного ярмарку кар’єри — ІЯКу від BEST Lviv!</b>"
            "Але мусимо зробити камінг-аут: цього року <b>ІЯК став віртуалом.</b> 😳 Немає часу пояснювати. Ти, головне, реєструйся. Далі — більше"
        )

        content.user_start_text = "Прив"
        content.user_start_photo = self.TEST_PHOTO
        content.ejf_start_text = (
            "Я знаю, друже, що до 19 травня ще є трохи часу, тому приготував для тебе кілька корисних штук. Заходь у <b>меню</b>, читай, слідкуй за оновленнями 🧐\n\n"
            "Почувай себе, як вдома ☺️"
        )
        content.ejf_start_photo = self.TEST_PHOTO
        content.save()

        # create ejf table
        ejf = JobFair()
        ejf.filters_interest = ["Full Stack", "Front End", "Data Science"]
        ejf.filters_experience = ["1 рік", "3+ років"]
        ejf.filters_employment = ["Full time", "Part time"]
        ejf.admin_password = "admin"
        ejf.cv_archive_file_id_list = []
        ejf.cv_archive_last_update = None
        ejf.cv_archive_size = 0
        ejf.start_menu = [
            SimpleButton(
                name="Що? 🤨",
                text=(
                    "<b>Інженерний ярмарок кар’єри — коротко ІЯК — це must-visit подія для кожного студента.</b> Не лякайся слова “інженерний”, бо наш Ярмарок уже давно вийшов за будь-які рамки і навіть претендує називатися наймасштабнішим у Львові.\n\n"
                    "У нас для цього є все:\n\n"
                    "✅ <b>Топ-компанії</b>, які зацікавлені в студентах. Чекни розділ 'Компанії'.\n\n"
                    "✅ Класний <b>контент</b>, який за два дні допоможе тобі нарешті відповісти на питання, ким ти хочеш стати. Ознайомся з розділом 'Розклад'.\n\n"
                    "✅ Можливість знайти <b>роботу</b> прямо через бота, тобто через мене! Після 20 травня я оновлю меню і ти все зрозумієш.\n\n"
                    "✅ Найкращі <b>учасники</b>. Угу, такі як ти!😌\n\n"
                    "Останні штрихи й ІЯК 2021 стане реальністю. Ще й не простою, а віртуальною. <b>Зустрінемося на Hopin!</b>\n\n"
                    "Па!"
                ),
                photo=self.TEST_PHOTO,
            ),
            SimpleButton(
                name="Де і як? 🦦",
                text=(
                    "Пам’ятаєш, ще на початку я казав, що ІЯК став віртуалом? Так-от, я мав на увазі, що цього року у Львівській політехніці звичного Ярмарку не буде. Не буде довгих черг, великих скупчень і хаосу. <b>Ми переїжджаємо в кращі санітарні умови... В онлайн простір!</b>✌️👩‍💻\n\n"
                    "ІЯК відбудеться на платформі <b>Hopin</b>. Ти майже не відчуєш різниці між спілкуванням наживо і онлайн. На Hopin усе організовано так, як ми звикли: віртуальні стенди з компаніями, окрема кімната для презентацій та воркшопів. Є навіть сцена!\n\n"
                    "<b>Переходь за посиланням у запрошенні і побач усе на власні очі.</b>"
                ),
                photo=self.TEST_PHOTO,
            ),
            SimpleButton(
                name="Компанії 📈",
                text="КомпаніїКомпаніїКомпанії",
                photo=self.TEST_PHOTO,
                url_link="https://ejf.best-lviv.org.ua/partners/ejfwp/",
                url_text="Детально про компанії",
            ),
            SimpleButton(
                name="Розклад 📌",
                text="РозкладРозкладРозклад",
                photo=self.TEST_PHOTO,
            ),
            SimpleButton(
                name="Зв'язок з нами ✍️",
                text=(
                    "🙂Залишилися питання? Може, маєш важливий фідбек на цьому етапі? У такому разі напиши комусь з нас🙃\n\n"
                    "<b>Вибирай:</b>\n\n"
                    "<a href='https://t.me/Slavkoooo'>головний організатор Ярік</a>\n\n"
                    "<a href='https://t.me/PogibaAnn'>відповідальна за компанії Аня</a>\n\n"
                    "<a href='https://t.me/OnAzart'>відповідальний за компанії Назар</a>\n\n"
                    "<a href='https://t.me/Yaroslav_Horodyskyi'>відповідальний за технічну частину Ярік</a>\n\n"
                    "<a href='https://t.me/demberetska'>відповідальна за контент Соля</a>\n\n"
                    "<a href='https://t.me/foxiero'>відповідальна за дизайн Софа</a>\n\n"
                    "<a href='https://t.me/vikahbhk'>відповідальна за піар Віка</a>\n\n"
                    "<a href='https://t.me/yarchik_5'>відповідальна за людські ресурси Ярина</a>\n\n"
                ),
                photo=self.TEST_PHOTO,
            ),
        ]
        ejf.content = content
        ejf.start_datetime = datetime(2021, 5, 19, 10, 0, 0)
        ejf.end_datetime = self.JOB_FAIR_END_TIME
        ejf.save()

    def update_ejf_table(self):
        ejf = self.get_ejf()

        # form paragraphs in ejf menu
        for btn in ejf.start_menu:
            btn.name = btn.name.replace("\\n", "\n")
            btn.text = btn.text.replace("\\n", "\n")

        # form paragraphs in content
        content = ejf.content
        ejf.content.start_text = content.start_text.replace("\\n", "\n")
        ejf.content.user_start_text = content.user_start_text.replace("\\n", "\n")
        ejf.content.ejf_start_text = content.ejf_start_text.replace("\\n", "\n")

        ejf.content.save()
        ejf.save()

    def update_quiz_table(self):
        quizes = Quiz.objects

        # form paragraphs in questions
        for quiz in quizes:
            for question in quiz.questions:
                question.message = question.message.replace("\\n", "\n")

            quiz.save()

    def get_ejf(self):
        return JobFair.objects.first()

    def get_cv_count(self) -> int:
        return User.objects.filter(cv_file_id__ne=None).count()

    def update_deleted_users(self):
        pass

    # HZ CHI TREBA
    def _add_test_user(
        self,
        chat_id,
        name,
        surname,
        username,
        interests=[],
        experience="",
        employment="",
        apply_counter=0,
        registration_date=None,
        last_update_date=None,
        last_interaction_date=None,
        hr_status=False,
    ):

        registration_date = datetime.now(tz=timezone.utc)
        last_interaction_date = registration_date
        last_update_date = registration_date

        User(
            chat_id=chat_id,
            name=name,
            surname=surname,
            username=username,
            interests=interests,
            experience=experience,
            employment=employment,
            apply_counter=apply_counter,
            registration_date=registration_date,
            last_update_date=last_update_date,
            last_interaction_date=last_interaction_date,
            hr_status=hr_status,
        ).save()

    def _generate_string(self, long=False):
        letters = string.ascii_letters
        if long is False:
            length = random.randint(10, 30)
        else:
            length = random.randint(300, 500)

        return "".join(random.choice(letters) for i in range(length))

    def _create_telegraph_account(self):
        SHORT_NAME = "BEST Job Fest"
        AUTHOR_NAME = "BEST Lviv"
        AUTHOR_URL = "https://t.me/bestlviv"

        ejf = self.get_ejf()

        if ejf.telegraph_token is None:
            self.telegraph = Telegraph()
            self.telegraph.create_account(SHORT_NAME, AUTHOR_NAME, AUTHOR_URL)

            # save new token
            ejf.update(set__telegraph_token=self.telegraph.get_access_token())
            ejf.save()

            print("New Telegraph account has been initialized")

        else:
            self.telegraph = Telegraph(ejf.telegraph_token)

            print("Telegraph account has been initialized")


class Content(me.Document):
    start_text = me.StringField()
    start_photo = me.StringField()
    user_start_text = me.StringField()
    user_start_photo = me.StringField()
    ejf_start_text = me.StringField()
    ejf_start_photo = me.StringField()


class SimpleButton(me.EmbeddedDocument):
    name = me.StringField()
    text = me.StringField()
    photo = me.StringField()
    url_link = me.StringField()
    url_text = me.StringField()


class JobFair(me.Document):
    filters_interest = me.ListField(default=list())
    filters_experience = me.ListField(default=list())
    filters_employment = me.ListField(default=list())
    admin_password = me.StringField()
    telegraph_token = me.StringField()
    cv_archive_file_id_list = me.ListField(default=None)
    cv_archive_last_update = me.DateTimeField(default=None)
    cv_archive_size = me.IntField(default=0)
    start_menu = me.ListField(me.EmbeddedDocumentField(SimpleButton), default=list())
    content = me.ReferenceField(Content)
    start_datetime = me.DateTimeField()
    end_datetime = me.DateTimeField()


class User(me.Document):
    chat_id = me.IntField(required=True, unique=True)
    name = me.StringField(required=True)
    surname = me.StringField(required=True)
    username = me.StringField(required=True)
    interests = me.ListField(default=list())
    experience = me.ListField(default=list())
    employment = me.ListField(default=list())
    cv_file_id = me.StringField(default=None)
    cv_file_name = me.StringField(default=None)
    apply_counter = me.IntField(default=20)
    additional_info = me.DictField(default=None)
    register_source = me.StringField(default="Unknown")
    registration_date = me.DateTimeField(required=True)
    last_update_date = me.DateTimeField(required=True)
    last_interaction_date = me.DateTimeField(required=True)
    hr_status = me.BooleanField(default=False)
    is_blocked = me.BooleanField(default=False)


class Company(me.Document):
    name = me.StringField(required=True, unique=True)
    photo_id = me.StringField(required=True)
    description = me.StringField(required=True)
    company_url = me.StringField()
    vacancy_counter = me.IntField(default=20)  # ?
    promote_counter = me.IntField(default=1)
    HR = me.ReferenceField(User, required=False)
    token = me.StringField(required=True)
    registration_date = me.DateTimeField(required=True)
    # vacancy_list = me.ListField(me.EmbeddedDocumentField, Vacancy, required=False)


class Vacancy(me.Document):
    company = me.ReferenceField(Company, required=True)
    name = me.StringField(required=True)
    tag = me.StringField(required=True)
    salary = me.StringField(required=True)
    experience = me.StringField(required=True)
    employment_type = me.StringField(required=True)
    description = me.StringField(required=True)
    telegraph_link_token = me.StringField()
    add_date = me.DateTimeField(required=True)
    last_update_date = me.DateTimeField(required=True)
    active_days_left = me.IntField(default=14)
    is_active = me.BooleanField(default=True)

    @staticmethod
    def get_editable_field_info() -> dict:
        return {
            "tag": "Категорія",
            "salary": "Заробітня плата",
            "experience": "Досвід роботи",
            "employment_type": "Тип працевлаштування",
            "description": "Опис",
        }


class Question(me.EmbeddedDocument):
    name = me.StringField(required=True)
    message = me.StringField(required=True)
    # photo = me.StringField(default=None)
    buttons = me.ListField(default=list())
    input_type = me.StringField(choices=["text", "photo", "contact"], default="text")
    max_text_size = me.IntField(max_value=4000)
    allow_user_input = me.BooleanField(default=True)
    regex = me.StringField(default=None)
    correct_answer_message = me.StringField(defaul=None)
    wrong_answer_message = me.StringField(default="Неправильний формат!")


class Answer(me.EmbeddedDocument):
    pass


class Quiz(me.Document):
    name = me.StringField(required=True)
    questions = me.ListField(me.EmbeddedDocumentField(Question), default=list())
    is_required = me.BooleanField(default=False)


# class VacancyPreviewLog(me.Document):
#    """
#    Class for logging user viewing of vacancy.
#    """
#
#    vacancy = me.ReferenceField(Vacancy, required=True)
#    user = me.ReferenceField(User, required=True)
#    log_datetime = me.DateTimeField(required=True)
#


class VacancyApplyLog(me.Document):
    """
    Class for logging any applying for a job.
    """

    vacancy = me.ReferenceField(Vacancy, required=True)
    user = me.ReferenceField(User, required=True)
    apply_datetime = me.DateTimeField(required=True)
    last_view_datetime = me.DateTimeField(default=None)
    view_count = me.IntField(default=0)


# class VacancyPromotionLog(me.Document):
#    """
#    Class for logging every promotion.
#    """
#
#    vacancy = me.ReferenceField(Vacancy, required=True)
#    auditory_tag = me.StringField(required=True)
#    log_datetime = me.DateField(required=True)


# from datetime import datetime
#
# if __name__ == '__main__':
#    #table1 = User().save()  # insert new user in table
#
#    me.connect(host="mongodb+srv://HYaroslav:4486@ejfcluster.jdquq.mongodb.net/ejf_vacancy_bot?retryWrites=true&w=majority")
#
#    now = datetime.now()
#
#    user = User()
#    user.chat_id = 12312
#    user.name = "Yaroslav"
#    user.surname = "Horodyskyi"
#    user.username = "@Yaroslav_Horodyskyi"
#    user.registration_date = now
#    user.last_update_date = now
#    user.last_interaction_date = now
#    try:
#        user.save()
#    except:
#        pass
#
#    company = Company()
#    company.name = "SoftServe"
#    company.photo_id = "afadfasdf"
#    company.description = "hahaaahahha"
#    company.token = "afafe13f23f3"
#    company.registration_date = now
#    try:
#        company.save()
#    except:
#        pass
#
#    vacancy = Vacancy()
#    vacancy.company = Company.objects.filter(name="SoftServe")[0]
#    vacancy.name = "Strong Middle Python developer"
#    vacancy.tag = "python"
#    vacancy.salary = "1000-2000$"
#    vacancy.experience = "10 років"
#    vacancy.employment_type = "Full Time"
#    vacancy.description = """Requirements:
#
# 4+ years of experience in Python development;Experience in Django, Postgre, SQL,;Build REST API for Database CRUD Operations;Understanding Python deployment flow (django, wsgi, nginx, heroku etc.);Experience with Linux, bash scripting;Experience with CI/CD pipelines and devops practices for Python developments;Ability unit/integration tests.Experience with Swagger and Git Hub
#
# Duties:
#
# Development of projects from scratch
# Development of project modules.
# Writing an API.
# Supporting of ready projects
# Terms:
#
# Basic communication in Telegram (you need to be in touch with some of our distant workers).
# Working in a team of programmers.
# Using Trello task manager
# Git Hub
# Additional info:
#
# Please be ready to do testing task before the interview"""
#    vacancy.add_date = now
#    vacancy.last_update_date = now
#    #vacancy.save()
#    try:
#        pass
#        #vacancy.save()
#    except:
#        pass
#
#    #cv = CV()
#    #cv.cv_file = open("cv.pdf", "rb")
#    #cv.add_date = now
#    #cv.last_update_date = now
#    #cv.save()
##
#    #user = User.objects.with_id("605fae402abdd4962ae12c20")
##
#    #user.cv = cv
#    #user.save()
#
#
#    log = VacancyApplyLog()
#    log.vacancy = Vacancy.objects.with_id("605fbd8a7e6e123aa296f234")
#    log.user = User.objects.with_id("605fae402abdd4962ae12c20")
#    log.cv = CV.objects.with_id("605fbee7d2484091d578464f")
#    log.log_datetime = now
#    log.save()
#
#
#
#
#
#
#    #for u in User.objects:
#    #    print(len(str(u.id)))
#
#
#    #vac1 = Vacancy()
#    #vac2 = Vacancy()
#    #vacancies = [vac1, vac2]
#    #table2 = Company(name='Salam', photo_id='1', description='fff', vacancy_counter='5', HR_chat_id='1',
#    #                 token='urhfhsf1', registration_date='2012-02-02', vacancy_list=vacancies).save()
#    #table4 = VacancyPreviewLog().save()
#    #table5 = VacancyApplyLog().save()
#    #table6 = VacancyPromotionLog().save()
#

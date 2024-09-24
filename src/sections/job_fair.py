from telebot.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from ..data import User, Data, JobFair
from ..objects import quiz
from ..sections.section import Section
from ..staff import utils


class JobFairSection(Section):
    def __init__(self, data: Data):
        super().__init__(data)

        self.TEXT_BUTTONS = self._get_start_button_names()

    def process_text(self, text, user: User):
        self.send_button_content(user, text)

    def send_start_menu(self, user: User):
        ejf = self.data.get_ejf()
        self.TEXT_BUTTONS = self._get_start_button_names(ejf)

        start_message = ejf.content.ejf_start_text
        start_photo = ejf.content.ejf_start_photo
        markup = self._form_markup()

        self.bot.send_photo(
            user.chat_id,
            caption=start_message,
            photo=start_photo,
            reply_markup=markup,
        )

    def send_button_content(self, user: User, btn_text: str):
        ejf = self.data.get_ejf()

        for btn in ejf.start_menu:
            if btn.name == btn_text:
                # if content have link button
                markup = InlineKeyboardMarkup()
                if btn.url_link:
                    url_button = InlineKeyboardButton(
                        text=btn.url_text, url=btn.url_link
                    )
                    markup.add(url_button)

                self.bot.send_photo(
                    chat_id=user.chat_id,
                    photo=btn.photo,
                    caption=btn.text,
                    reply_markup=markup,
                )

    def _get_start_button_names(self, ejf: JobFair = None) -> list:
        if ejf is None:
            ejf = self.data.get_ejf()

        button_names = list()

        for button in ejf.start_menu:
            button_names += [button.name]

        return button_names

    def _form_markup(self) -> ReplyKeyboardMarkup:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

        for btn_row in utils.reply_keyboard_columns_generator(
            btn_names_list=self.TEXT_BUTTONS, col=2
        ):
            keyboard.row(*btn_row)

        return keyboard

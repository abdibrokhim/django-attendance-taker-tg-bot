# start
# import below, to work Telegram Bot with Django Rest Framework properly
import sys
sys.dont_write_bytecode = True

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from app import models

from asgiref.sync import sync_to_async
# end

import logging
import keys
from datetime import datetime
import pytz

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Stages
START_ROUTES, END_ROUTES = range(2)
# Callback data
PLUS, MINUS, DONE = range(3)

users_arr = []
users_dict = {}


def get_time():
    current_time = datetime.now(pytz.timezone('Asia/Tashkent'))
    return current_time.strftime('%Y-%m-%d %H:%M:%S')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send message on `/start`."""

    # Get user that sent /start and log his name
    user = update.effective_chat
    logger.info("User %s started the conversation.", user.username)

    keyboard = [
        [
            InlineKeyboardButton("+", callback_data=str(PLUS)),
            InlineKeyboardButton("-", callback_data=str(MINUS)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Start handler, Choose a route", reply_markup=reply_markup)

    return START_ROUTES


async def plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirm button"""

    user = update.effective_chat
    # if user.username not in users:
    # testing using dict
    users_arr.append(user.username)
    users_dict['user_id'] = user.id
    users_dict['username'] = user.username
    users_dict['fullname'] = user.full_name
    users_dict['arrived_at'] = get_time()
    users_dict['left_at'] = None

    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text="Confirm", reply_markup=keyboard()
    )

    await post_person(user)
    # person = models.Person(tg_id=user.id,
    #                        tg_username=user.username,
    #                        tg_fullname=user.full_name,
    #                        arrived_at=get_time(),
    #                        )
    # person.save()

    return END_ROUTES


@sync_to_async
def post_person(user):
    models.Person(
        tg_id=user.id,
        tg_username=user.username,
        tg_fullname=user.full_name,
        arrived_at=get_time(),
    ).save()


@sync_to_async
def put_person(user, user_id):
    models.Person.objects.select_related().filter(pk=user_id, tg_id=user.id).update(left_at=get_time())


@sync_to_async
def left_none(user):
    active_id = models.Person.objects.select_related()\
        .filter(tg_id=user.id, left_at=None).values_list("pk", flat=True).last()
    if active_id:
        return True
    else:
        return False


@sync_to_async
def active_id(user):
    person_id = models.Person.objects.select_related() \
        .filter(tg_id=user.id, left_at=None).values_list("pk", flat=True).last()
    print('active_id:', active_id)
    print('type:', type(active_id))
    if person_id:
        return person_id
    else:
        return False


async def minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirm button"""

    user = update.effective_chat
    if left_none(user):
    # if user.username in users_arr and users_dict['left_at'] is None:
        users_arr.append(user)

        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            text="Confirm", reply_markup=keyboard()
        )

        users_dict['left_at'] = get_time()
        ac_id = active_id(user)
        print('ac_id:', ac_id)
        await put_person(user, ac_id)

        return END_ROUTES
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text="+ then -")


def keyboard():
    keyboard = [
        [
            InlineKeyboardButton("DONE", callback_data=str(DONE)),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")
    print(users_arr)
    print(users_dict)
    return ConversationHandler.END


def main():
    """Run the bot."""
    application = Application.builder().token(keys.TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(plus, pattern="^" + str(PLUS) + "$"),
                CallbackQueryHandler(minus, pattern="^" + str(MINUS) + "$"),
            ],
            END_ROUTES: [
                CallbackQueryHandler(end, pattern="^" + str(DONE) + "$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == "__main__":
    main()

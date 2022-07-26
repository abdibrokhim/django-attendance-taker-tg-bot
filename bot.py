# import below, to work Telegram Bot with Django Rest Framework properly
# start
import sys
import time

sys.dont_write_bytecode = True

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from app import models, serializers

from asgiref.sync import sync_to_async
# end

import logging
from datetime import datetime
import pytz
from config import settings
import pandas

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update)

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

# States
START_STATE, END_STATE = range(2)

# Callback data
PLUS, MINUS = range(2)


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
def get_last_id(user):
    last_id = models.Person.objects.select_related() \
        .filter(tg_id=user.id, left_at=None).values_list("pk", flat=True).last()
    active_id = models.Person.objects.select_related() \
        .filter(tg_id=user.id).values_list("pk", flat=True).last()
    if last_id >= active_id:
        return last_id
    else:
        return False


@sync_to_async
def get_data():
    persons = models.Person.objects.all()
    serializer = serializers.PersonSerializer(persons, many=True)

    all_data = []
    for i in range(0, len(serializer.data)):
        data = []
        data.append(serializer.data[i]['tg_fullname'])
        data.append(serializer.data[i]['arrived_at'])
        data.append(serializer.data[i]['left_at'])
        print('-'*50)
        print(data)
        all_data.append(data)

    print('-'*50)
    print(all_data)

    return all_data


def set_data(info):
    pandas.DataFrame(data=info, columns=['name', 'arrived', 'left']).to_excel('report.xlsx', )
    return 1


def get_time():
    current_time = datetime.now(pytz.timezone(settings.TIME_ZONE))
    return current_time.strftime('%Y-%m-%d %H:%M:%S')


# def send_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     update.message.reply_document(open('report.xlsx'), 'r')


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_data = await get_data()

    if set_data(active_data):
        await update.message.reply_document(open('report.xlsx'),)

    time.sleep(2)
    os.remove('report.xlsx')

    return END_STATE


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send message on `/start`."""

    # Get user that sent /start and log his name
    user = update.effective_user
    logger.info("User %s started the conversation.", user.username)

    keyboard = [
        [
            InlineKeyboardButton("+", callback_data=str(PLUS)),
            InlineKeyboardButton("-", callback_data=str(MINUS)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Choose an option", reply_markup=reply_markup,)

    return START_STATE


async def plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirm button"""

    user = update.effective_user
    query = update.callback_query
    await query.answer(text='Saved')

    message = await query.edit_message_text(text=".")
    await context.bot.delete_message(message.chat.id, message.message_id)

    await post_person(user)

    return END_STATE


async def minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirm button"""

    user = update.effective_user
    active_user_id = await get_last_id(user)

    if active_user_id:
        query = update.callback_query
        await query.answer(text="Saved")

        message = await query.edit_message_text(text=".")
        await context.bot.delete_message(message.chat.id, message.message_id)

        print('-'*50)
        print('active_user_id:', active_user_id)
        await put_person(user, active_user_id)

        return END_STATE
    else:
        query = update.callback_query
        await query.answer(text="+ then -")


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    return ConversationHandler.END


def main():
    """Run the bot."""
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler('report', report)],
        states={
            START_STATE: [
                CallbackQueryHandler(plus, pattern="^" + str(PLUS) + "$"),
                CallbackQueryHandler(minus, pattern="^" + str(MINUS) + "$"),
            ],
            END_STATE: [
                CallbackQueryHandler(end),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    # application.add_handler(CommandHandler('report', report))

    application.run_polling()


if __name__ == "__main__":
    main()

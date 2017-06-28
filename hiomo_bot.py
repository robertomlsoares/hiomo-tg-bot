#!/usr/bin/env python3
# coding: utf-8

"""
    hiomo_bot.py
    ~~~~~~~~~~~~

    HiomoBot is a Telegram bot that will send you messages containing the lunch menu of the day from the
    Hiomotie 32 Sodexo restaurant.

    :copyright: (c) 2017 by Roberto Soares, Minna Svartbäck
    :license: MIT
"""

import datetime
import logging
import os
from uuid import uuid4

import requests
from telegram import InlineQueryResultArticle, InputTextMessageContent, ParseMode
from telegram.ext import Updater, CommandHandler, InlineQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

open_text = """Summer Opening Hours 3.7. - 4.8.
Restaurant Open: 8:00 - 14:30
Lunch Served: 11:00 - 13:30"""
help_text = """You can control me by sending me these commands:

/food - I'll tell you the complete menu of the day.
/fooden - I'll tell you the complete menu of the day in English only.
/foodfi - I'll tell you the complete menu of the day in Finnish only.
/open - I'll tell you the opening hours of the staff restaurant.
/subscribe - I'll send you a message everyday with the complete menu of the day.
/unsubscribe - I'll stop sending you a message everyday."""


def start(bot, update):
    """
    Initial message that the bot will send when a user starts a conversation.

    :param bot: Bot object.
    :param update: Telegram update event.
    """

    update.message.reply_text('Hi! I\'m HiomoBot! ' + help_text)


def help(bot, update):
    """
    Help message that will be displayed when the user calls /help.

    :param bot: Bot object.
    :param update: Telegram update event.
    """

    update.message.reply_text(help_text)


def food(bot, update):
    """
    Message with the complete menu of the day in both English and Finnish.

    :param bot: Bot object.
    :param update: Telegram update event.
    """

    message = _food_msg()
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


def subscribed_food(bot, job):
    """
    A message for the subscribers with the complete menu of the day in both English and Finnish.

    :param bot: Bot object.
    :param job: Job object.
    """

    message = _food_msg()
    bot.send_message(job.context, text=message, parse_mode=ParseMode.MARKDOWN)


def fooden(bot, update):
    """
    Message with the complete menu of the day in English only.

    :param bot: Bot object.
    :param update: Telegram update event.
    """

    message = _food_msg_en()
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


def foodfi(bot, update):
    """
    Message with the complete menu of the day in Finnish only.

    :param bot: Bot object.
    :param update: Telegram update event.
    """

    message = _food_msg_fi()
    update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


def open(bot, update):
    """
    Message containing opening hours of the restaurant. Hard coded because I'm lazy.

    :param bot: Bot object.
    :param update: Telegram update event.
    """

    update.message.reply_text(open_text, parse_mode=ParseMode.MARKDOWN)


def subscribe(bot, update, args, job_queue, chat_data):
    """
    This handler will subscribe a user to receive daily messages at 10:30 in the morning containing the complete menu
    of the day in both English and Finnish.

    :param bot: Bot object.
    :param update: Telegram update event.
    :param args: Arguments from the user.
    :param job_queue: Job Queue object created by the Updater.
    :param chat_data: Dict to keep any data related to the chat that the update was sent in.
    """

    chat_id = update.message.chat_id
    job = job_queue.run_daily(subscribed_food, datetime.time(10, 30), (0, 1, 2, 3, 4), context=chat_id)
    chat_data['job'] = job

    update.message.reply_text('You are now subscribed to HiomoBot! You will receive the menu everyday at 10:30 AM.')


def unsubscribe(bot, update, chat_data):
    """
    This handler will unsubscribe a user from HiomoBot daily messages.

    :param bot: Bot object.
    :param update: Telegram update event.
    :param chat_data: Dict to keep any data related to the chat that the update was sent in.
    """

    if 'job' not in chat_data:
        update.message.reply_text('You can\'t unsubscribe if you have no subscription.')
        return

    job = chat_data['job']
    job.schedule_removal()

    del chat_data['job']

    update.message.reply_text('You are now unsubscribed from HiomoBot.')


def inlinequery(bot, update):
    """
    Handler that will answer inline queries.

    :param bot: Bot object.
    :param update: Telegram update event.
    """

    results = []

    results.append(InlineQueryResultArticle(id=uuid4(),
                                            title="food",
                                            input_message_content=InputTextMessageContent(_food_msg()),
                                            parse_mode=ParseMode.MARKDOWN))
    results.append(InlineQueryResultArticle(id=uuid4(),
                                            title="fooden",
                                            input_message_content=InputTextMessageContent(_food_msg_en()),
                                            parse_mode=ParseMode.MARKDOWN))
    results.append(InlineQueryResultArticle(id=uuid4(),
                                            title="foodfi",
                                            input_message_content=InputTextMessageContent(_food_msg_fi()),
                                            parse_mode=ParseMode.MARKDOWN))
    results.append(InlineQueryResultArticle(id=uuid4(),
                                            title="open",
                                            input_message_content=InputTextMessageContent(open_text),
                                            parse_mode=ParseMode.MARKDOWN))

    update.inline_query.answer(results)


def error(bot, update, error):
    """
    Handler to log errors.

    :param bot: Bot object.
    :param update: Telegram update event.
    :param error: Error message.
    """

    logger.warning('Update "%s" caused error "%s"' % (update, error))


def _food_msg():
    """
    Helper function for the message string of the menu.

    :return: Menu of the day in both English and Finnish.
    """

    menu = _get_menu_today()

    message = ''
    for course in menu.get('courses', []):
        title_fi = course.get('title_fi', 'NA')
        title_en = course.get('title_en', 'NA')
        properties = course.get('properties', 'NA')
        category = course.get('category', None)

        if category == 'Dessert':
            message += '\n*Dessert:* %s.\n%s. %s\n' % (title_fi, title_en, properties)
        else:
            message += '\n%s.\n%s. %s\n' % (title_fi, title_en, properties)

    if message == '':
        message = 'No menu available today. Sorry!'
    return message


def _food_msg_en():
    """
    Helper function for the message string of the menu in English.

    :return: Menu of the day in English.
    """

    menu = _get_menu_today()

    message = ''
    for course in menu.get('courses', []):
        title_en = course.get('title_en', 'NA')
        properties = course.get('properties', 'NA')
        category = course.get('category', None)

        if category == 'Dessert':
            message += '\n*Dessert:* %s. %s\n' % (title_en, properties)
        else:
            message += '\n%s. %s\n' % (title_en, properties)

    if message == '':
        message = 'No menu available today. Sorry!'
    return message


def _food_msg_fi():
    """
    Helper function for the message string of the menu in Finnish.

    :return: Menu of the day in Finnish.
    """
    menu = _get_menu_today()

    message = ''
    for course in menu.get('courses', []):
        title_fi = course.get('title_fi', 'NA')
        properties = course.get('properties', 'NA')
        category = course.get('category', None)

        if category == 'Dessert':
            message += '\n*Dessert:* %s. %s\n' % (title_fi, properties)
        else:
            message += '\n%s. %s\n' % (title_fi, properties)

    if message == '':
        message = 'No menu available today. Sorry!'
    return message


def _get_menu_today():
    """
    Sends a GET request to receive the Sodexo menu of the day of Hiomotie 32.

    :return: Response of the request in JSON.
    """

    today = datetime.date.today()
    url = 'http://www.sodexo.fi/ruokalistat/output/daily_json/89/%s/%s/%s/fi' % (today.year, today.month, today.day)
    r = requests.get(url)
    return r.json()


def main():
    #: Remember to remove the real token when pushing to GitHub.
    TOKEN = 'TOKEN'
    PORT = int(os.environ.get('PORT', '5000'))

    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('food', food))
    dispatcher.add_handler(CommandHandler('fooden', fooden))
    dispatcher.add_handler(CommandHandler('foodfi', foodfi))
    dispatcher.add_handler(CommandHandler('open', open))
    dispatcher.add_handler(
        CommandHandler('subscribe', subscribe, pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dispatcher.add_handler(CommandHandler('unsubscribe', unsubscribe, pass_chat_data=True))

    dispatcher.add_handler(InlineQueryHandler(inlinequery))

    dispatcher.add_error_handler(error)

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.set_webhook('https://hiomo-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    main()

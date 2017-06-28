#!/usr/bin/env python3
# coding: utf-8

"""
HiomoBot will send daily Telegram messages to subscribers containing the Sodexo menu of the current day.
"""

from telegram.ext import Updater, CommandHandler, Job
import logging
import requests
import datetime
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

help_text = """You can control me by sending me these commands:

/food - I'll tell you the complete menu of the day.
/fooden - I'll tell you the complete menu of the day in English only.
/foodfi - I'll tell you the complete menu of the day in Finnish only.
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

    menu = _get_menu_today()

    message = ''
    for course in menu.get('courses', []):
        title_fi = course.get('title_fi', 'NA')
        title_en = course.get('title_en', 'NA')
        properties = course.get('properties', 'NA')

        message += '\nTitle (FI): %s.\nTitle (EN): %s\nProperties: %s\n' % (title_fi, title_en, properties)

    if message == '':
        message = 'No menu available today. Sorry!'
    update.message.reply_text(message)


def subscribed_food(bot, job):
    """
    A message for the subscribers with the complete menu of the day in both English and Finnish.

    :param bot: Bot object.
    :param job: Job object.
    """

    menu = _get_menu_today()

    message = ''
    for course in menu.get('courses', []):
        title_fi = course.get('title_fi', 'NA')
        title_en = course.get('title_en', 'NA')
        properties = course.get('properties', 'NA')

        message += '\nTitle (FI): %s.\nTitle (EN): %s\nProperties: %s\n' % (title_fi, title_en, properties)

    if message == '':
        message = 'No menu available today. Sorry!'
    bot.send_message(job.context, text=message)


def fooden(bot, update):
    """
    Message with the complete menu of the day in English only.

    :param bot: Bot object.
    :param update: Telegram update event.
    """

    menu = _get_menu_today()

    message = ''
    for course in menu.get('courses', []):
        title_en = course.get('title_en', 'NA')
        properties = course.get('properties', 'NA')

        message += '\nTitle: %s\nProperties: %s\n' % (title_en, properties)

    if message == '':
        message = 'No menu available today. Sorry!'
    update.message.reply_text(message)


def foodfi(bot, update):
    """
    Message with the complete menu of the day in Finnish only.

    :param bot: Bot object.
    :param update: Telegram update event.
    """

    menu = _get_menu_today()

    message = ''
    for course in menu.get('courses', []):
        title_fi = course.get('title_fi', 'NA')
        properties = course.get('properties', 'NA')

        message += '\nTitle: %s\nProperties: %s\n' % (title_fi, properties)

    if message == '':
        message = 'No menu available today. Sorry!'
    update.message.reply_text(message)


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


def error(bot, update, error):
    """
    Handler to log errors.

    :param bot: Bot object.
    :param update: Telegram update event.
    :param error: Error message.
    """

    logger.warning('Update "%s" caused error "%s"' % (update, error))


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
    dispatcher.add_handler(
        CommandHandler('subscribe', subscribe, pass_args=True, pass_job_queue=True, pass_chat_data=True))
    dispatcher.add_handler(CommandHandler('unsubscribe', unsubscribe, pass_chat_data=True))

    dispatcher.add_error_handler(error)

    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.set_webhook('https://hiomo-bot.herokuapp.com/' + TOKEN)
    updater.idle()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# coding: utf-8

"""
HiomoBot will send daily Telegram messages to subscribers containing the Sodexo menu of the current day.
"""

from telegram.ext import Updater, CommandHandler, Job
import logging
import requests
import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)


def start(bot, update):
    update.message.reply_text(
        'Hi! I\'m HiomoBot! You will receive a message everyday with the menu for the restaurant. '
        'If you wish to stop receiving them, use the /unsubscribe command.')


def food(bot, update):
    today = datetime.date.today()
    url = 'http://www.sodexo.fi/ruokalistat/output/daily_json/89/%s/%s/%s/fi' % (today.year, today.month, today.day)
    r = requests.get(url)
    response = r.json()

    message = ''
    for course in response.get('courses', []):
        title_fi = course.get('title_fi', 'NA')
        title_en = course.get('title_en', 'NA')
        properties = course.get('properties', 'NA')

        message += '\nTitle (FI): %s.\nTitle (EN): %s\nProperties: %s\n' % (title_fi, title_en, properties)

    if message == '':
        message = 'No menu available today. Sorry!'
    update.message.reply_text(message)


def subscribe(bot, update):
    pass


def unsubscribe(bot, update):
    pass


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    # Remember to remove the real token when pushing to GitHub.
    updater = Updater('TOKEN')

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('food', food))

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
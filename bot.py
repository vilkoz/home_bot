#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

from os import environ
import subprocess

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# dict for shared info
shared = {}
shared["subs"] = []
shared["users"] = []

# users tracking list
from data import USERS

# old scan function
def scanNetwork():
    res = [False] * len(USERS)
    try:
        output = subprocess.check_output("nmap -sP 192.168.0.1/24 | grep \"scan report for\" | awk '{print $5}'", shell=True)
        output1 = subprocess.check_output("arp -a | grep -v \\<incomplete\\> | awk '{print $2}' | tr -d \\(\\)", shell=True)
        print ("out: ", output)
        print ("out1: ", output1)
    except Exception:
        return res
    ips = output.decode().split("\n")
    ips += output1.decode().split("\n")
    print ("ips: ", ips)
    for i, user in enumerate(USERS):
        if user[1] in ips:
            res[i] = True
    print(res)
    return res;

# net scan function, returns bool list 
def chekUsers():
    res = [False] * len(USERS)
    for i, user in enumerate(USERS):
        try:
            output = subprocess.check_output("nmap -sP %s | grep \"Host is up\"" % user[1], shell=True)
            returnCode = 0
        except subprocess.CalledProcessError as e:
            output = e.output
            returnCode = e.returncode
        # print("output: ", output)
        logger.info("output: %s" % output)
        if not returnCode:
            res[i] = True
    return res

def subscribeCommand(bot, update):
    chat_id = update.message.chat.id
    if chat_id not in shared["subs"]:
        subs = shared["subs"]
        subs.append(chat_id)
        shared["subs"] = subs
        bot.sendMessage(chat_id=chat_id,
            text=("you have subscribed for notification!" + str(shared["subs"])))
    else:
        bot.sendMessage(chat_id=chat_id,
            text=("you already subscribed for notification!"))

def sendInfoToSubscribers(bot, job):
    logger.info("---Sending info---")
    oldUserStatus = shared["users"]
    # newStatus = scanNetwork()
    newStatus = chekUsers()
    print("users in job: ", shared["users"])
    print("subs in job: ", shared["subs"])
    if oldUserStatus != newStatus:
        string = ""
        for i in range(len(oldUserStatus)):
            if oldUserStatus[i] != newStatus[i]:
                string += USERS[i][0] + (" came" if newStatus[i] else " left") + " home\n"
        logger.info("Sending info to subs")
        print("subs in job: ", shared["subs"])
        for chatId in shared["subs"]:
            logger.info("Sending info to %s", chatId)
            bot.sendMessage(chat_id=chatId, text=string)
        shared["users"] = newStatus

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(bot, update):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(environ["TOKEN"])

    # init job_queue
    # for sendInfoToSubscribers
    j = updater.job_queue
    job_minute = j.run_repeating(sendInfoToSubscribers,
            interval=20,
            first=0)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("subscribe", subscribeCommand))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()

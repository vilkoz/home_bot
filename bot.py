#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import ReplyKeyboardMarkup
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
shared["subs"] = [117155777]
shared["users"] = {}
shared["admins"] = {}
shared["admins"]["Vilko"] = True

# users tracking list
from data import USERS

# list of avaliable commands
COMMAND_LIST = ['start', 'help', 'subscribe', 'scan_network', 'check_users', 'wake_home']
COMMAND_LIST_MD = [x.replace("_", "\_") for x in COMMAND_LIST]

# old scan function
def scanNetwork():
    try:
        output = subprocess.check_output("nmap 192.168.0.1/24", shell=True)
        output1 = subprocess.check_output("arp -a | grep -v \\<incomplete\\>", shell=True)
        print ("out: ", output)
        print ("out1: ", output1)
    except Exception as e:
        return str(e)
    ips = output.decode()
    ips += output1.decode()
    return ips

# net scan function, returns bool list 
def checkUsers():
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

def checkAccessRights(update):
    if update.effective_user.username not in shared["admins"]:
        update.message.reply_text("You can't perform this action")
        return False
    return True

def wakeHomeCommand(bot, update):
    if not checkAccessRights(update):
        return
    try:
        output = subprocess.check_output("wol 40:61:86:eb:ab:58", shell=True)
        returnCode = 0
    except subprocess.CalledProcessError as e:
        output = e.output
        returnCode = e.returncode
    update.message.reply_text('```' + output.decode() + '```', parse_mode="Markdown")

def scanNetworkCommand(bot, update):
    if not checkAccessRights(update):
        return
    update.message.reply_text("Starting scan network..")
    s = scanNetwork()
    update.message.reply_text("```" + s + "```", parse_mode="Markdown")

def checkUsersCommand(bot, update):
    if not checkAccessRights(update):
        return
    update.message.reply_text("Starting check users..")
    res = checkUsers()
    string = ""
    for i, user in enumerate(USERS):
        string += "%s %s home\n" % (user[0], ("is" if res[i] else "not in"))
    update.message.reply_text(string)


def subscribeCommand(bot, update):
    if not checkAccessRights(update):
        return
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
    newStatus = checkUsers()
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
            if len(string):
                bot.sendMessage(chat_id=chatId, text=string)
        shared["users"] = newStatus

# send custom keyboard with commands
def keyboardStart(bot, update, text):
    chat_id = update.message.chat.id
    custom_keyboard = [["/" + x] for x in COMMAND_LIST]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=chat_id, 
                     text=text, 
                     reply_markup=reply_markup)

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! See /help for more info\n')


def help(bot, update):
    """Send a message when the command /help is issued."""
    reply = "**Avaliable commands:**\n"
    reply += "\n".join(["/" + x for x in COMMAND_LIST_MD])
    bot.send_message(chat_id=update.message.chat.id, text=reply, parse_mode="Markdown")
    keyboardStart(bot, update, "press what you want on keyboard")


def echo(bot, update):
    """Echo the user message."""
    keyboardStart(bot, update, "just press on keyboard")
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
            interval=600,
            first=0)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("subscribe", subscribeCommand))
    dp.add_handler(CommandHandler("scan_network", scanNetworkCommand))
    dp.add_handler(CommandHandler("check_users", checkUsersCommand))
    dp.add_handler(CommandHandler("wake_home", wakeHomeCommand))

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

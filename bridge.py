#!/usr/bin/env python
import HTMLParser
import logging
import os
import signal
import time

import irc, irc.bot
import websocket

from ChatExchange.SEChatWrapper import SEChatWrapper


logging.basicConfig(level=logging.DEBUG)

IRC_SERVER = os.environ.get('IRC_SERVER', 'cs1692x.moocforums.org')
IRC_PORT = int(os.environ.get('IRC_PORT', 6667))
IRC_CHANNEL = os.environ.get('IRC_CHANNEL', '#jb_test') # '#CS_CS169.1x'
IRC_NICK = os.environ.get('IRC_NICK', 'STACKEX')
IRC_SILENT = os.environ.get('IRC_SILENT', 'False').lower() != 'false'

SE_HOST = os.environ.get('SE_HOST', 'SO')
SE_USER_ID = int(os.environ['SE_USER_ID'])
SE_OPENID_USER = os.environ['SE_CHAT_USERNAME']
SE_OPENID_PASSWORD = os.environ['SE_OPENID_PASSWORD']
SE_ROOM_ID = int(os.environ.get('SE_ROOM_ID', 51082))


h = HTMLParser.HTMLParser()


class Bot(irc.bot.SingleServerIRCBot):
    def __init__(self):
        irc.bot.SingleServerIRCBot.__init__(
            self, [(IRC_SERVER, IRC_PORT)], IRC_NICK, IRC_NICK)

        self.se = SEChatWrapper(SE_HOST)
        self.se.login(SE_OPENID_USER, SE_OPENID_PASSWORD)
        self.se.joinRoom(SE_ROOM_ID)
        self.se.watchRoom(SE_ROOM_ID, self.on_se_message, 5)

    def on_se_message(self, message, chat):
        if IRC_SILENT:
            return

        if message['user_id'] != SE_USER_ID or not message['content'].startswith('<b>['):
            message_remaining = h.unescape(message['content'])

            # we split long messages so the IRC server doesn't complin
            self.connection.notice(IRC_CHANNEL,
                "%s: %s" % (
                    message['user_name'], message_remaining[:256]
                )
            )

            message_remaining = message_remaining[256:]

            while message_remaining:
                self.connection.notice(IRC_CHANNEL,
                    "%s [ctn'd]: %s" % (
                        message['user_name'], message_remaining
                    )
                )
                
                message_remaining = message_remaining[256:]

    def on_welcome(self, c, event):
        c.join(IRC_CHANNEL)
        self.se.sendMessage(SE_ROOM_ID, 
            "**[Connected to IRC and Joined Channel: %s:%s/%s]**" % (
                IRC_SERVER, IRC_PORT, IRC_CHANNEL))

    def _on_disconnect(self, *a, **kw):
        self.se.sendMessage(SE_ROOM_ID, 
            "**[Disconnected from IRC Server]**")
        return super(Bot, self)._on_disconnect(*a, **kw)

    def _on_kick(self, *a, **kw):
        self.se.sendMessage(SE_ROOM_ID, 
            "**[Kicked from IRC Channel]**")
        return super(Bot, self)._on_kick(*a, **kw)

    def on_pubmsg(self, connection, event):
        if IRC_NICK not in event.source.nick:
            body = event.arguments[0]
            self.se.sendMessage(SE_ROOM_ID, 
                "**[IRC] %s:** %s" % (event.source.nick, body,))


def main():
    bot = Bot()

    def on_int(signal, frame):
        bot.disconnect()
        time.sleep(5) # allow for parting Stack Exchange chat message to be sent


    signal.signal(signal.SIGINT, on_int)
    bot.start()


if __name__ == '__main__':
    main()

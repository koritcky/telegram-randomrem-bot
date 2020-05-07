import schedule
import time
from threading import Thread
from users_db import Users
import queue
import random


class MyThread(Thread):
    def __init__(self, chat_id, users: Users, bot):
        self.changes_queue = queue.Queue()
        self.chat_id = chat_id
        self.users = users
        self.bot = bot

        self.create_schedule()
        self.is_active = 1
        super().__init__(target=self.scheduler, args=(self.changes_queue,))
        self.start()

    def scheduler(self, changes_queue):

        while True:
            try:
                changes = changes_queue.get(timeout=0.1)
                self.apply_changes(changes)
            except queue.Empty:
                pass

            if self.is_active:
                schedule.run_pending()

            time.sleep(1)

    def create_schedule(self):
        period = self.users.select(self.chat_id, 'period')
        reminders = self.users.select(self.chat_id, 'reminders')

        disp = 0.2
        start = (1 - disp) * period
        end = (1 + disp) * period

        schedule.every(start).to(end).seconds.do(self.send, self.bot, self.chat_id, reminders).tag(self.chat_id)

    def apply_changes(self, changes):
        if changes == 'status':
            self.is_active = self.users.select(self.chat_id, changes)
        if (changes == 'period') or (changes == 'reminders'):
            schedule.clear(self.chat_id)
            self.create_schedule()


    def send(self, bot, chat_id, reminders):
        try:
            bot.send_message(chat_id, random.choice(reminders))
        except IndexError:
            bot.send_message(chat_id, "I have nothing to send you, so I go *sleeping*. "  
                                      "Add a reminder and /activate me",
                             parse_mode='markdown')
            self.users.update(chat_id, 'status', 0)
            self.is_active = 0
# def do_changes(changes):
#     if changes == 'state':

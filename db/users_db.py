import sqlite3
import pickle

class Users:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

        self.columns = ['reminders', 'period', 'status', 'active_time']

        if database == ':memory:':
            # Create the table
            self.cursor.execute('''
                CREATE TABLE users(
                chat_id integer,
                reminders blob,
                period real,
                status integer,
                active_time text, 
                UNIQUE(chat_id)
            )''')


    def insert(self, chat_id, reminders, period, status=1, active_time='10:00-22:00'):
        """
        Creates new user
        :param chat_id: users's chat_id
        :param reminders: list of users' reminders
        :param period: period of sending
        :param status: current status
        :return:
        """
        with self.connection:
            try:
                self.cursor.execute("INSERT INTO users VALUES (:chat_id, :reminders, :period, :status, :active_time)", {
                    'chat_id': chat_id, 'reminders': pickle.dumps(reminders), 'period': period, 'status': status, 'active_time': active_time
                })
            except sqlite3.IntegrityError:
                pass

    def select(self, chat_id, column):
        if column in self.columns:
            with self.connection:
                result = self.cursor.execute(f"SELECT {column} FROM users WHERE chat_id={chat_id}").fetchone()[0]
                if column == 'reminders':
                    result = pickle.loads(result)
            return result
        else:
            raise Warning(f"Choose from existing variants: {str(self.columns)}")

    def update(self, chat_id, column, new_value):
        if column in self.columns:
            with self.connection:
                if column =='reminders':
                    new_value = pickle.dumps(new_value)
                self.cursor.execute(f'UPDATE users SET {column}=:new_value WHERE chat_id=:chat_id',
                                    {'chat_id': chat_id, 'new_value': new_value})
        else:
            raise Warning(f"Choose from existing variants: {str(self.columns)}")

    def add_reminder(self, chat_id, reminder):
        list = self.select(chat_id, 'reminders')

        if reminder not in list:
            list.append(reminder)
        else:
            raise ValueError(f'\"{reminder}\" reminder already exists')

        list = pickle.dumps(list)
        with self.connection:
            self.cursor.execute(f'UPDATE users SET reminders= :reminders WHERE chat_id=:chat_id',
                                {'reminders': list, 'chat_id': chat_id})

    def remove_reminder(self, chat_id, reminder):
        list = self.select(chat_id, 'reminders')

        if reminder in list:
            list.remove(reminder)
        else:
            raise ValueError(f'\"{reminder}\" reminder does not exist')

        list = pickle.dumps(list)
        with self.connection:
            self.cursor.execute(f'UPDATE users SET reminders= :reminders WHERE chat_id=:chat_id',
                                {'reminders': list, 'chat_id': chat_id})


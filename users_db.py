import sqlite3
import pickle

class Users:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

        if database == ':memory:':
            # Create the table
            self.cursor.execute('''
                CREATE TABLE users(
                chat_id integer,
                reminders blob,
                period real,
                status integer,
                UNIQUE(chat_id)
            )''')


    def select_all(self):
        """
        Get all data from table
        """
        with self.connection:
            return self.cursor.execute("SELECT * FROM users").fetchall()


    def insert(self, chat_id, reminders, period, status=1):
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
                self.cursor.execute("INSERT INTO users VALUES (:chat_id, :reminders, :period, :status)", {
                    'chat_id': chat_id, 'reminders': pickle.dumps(reminders), 'period': period, 'status': status
                })
            except sqlite3.IntegrityError:
                pass

    def select(self, chat_id, column):
        if column in ['reminders', 'period', 'status']:
            with self.connection:
                result = self.cursor.execute(f"SELECT {column} FROM users WHERE chat_id={chat_id}").fetchone()[0]
                if column == 'reminders':
                    result = pickle.loads(result)
            return result
        else:
            raise Warning("Choose from existing variants: 'reminders', 'period', 'status")

    def update(self, chat_id, column, new_value):
        if column in ['reminders', 'period', 'status']:
            with self.connection:
                if column =='reminders':
                    new_value = pickle.dumps(new_value)
                self.cursor.execute(f'UPDATE users SET {column}=:new_value WHERE chat_id=:chat_id',
                                    {'chat_id': chat_id, 'new_value': new_value})
        else:
            raise Warning("Choose from existing variants: 'period', 'status'")

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
# users = Users(':memory:')
# chat_id = 6456546
# users.insert(chat_id, ['Meditate', 'Breathe!'], 5, 1)
# print(users.select(chat_id, 'period'))
# users.update(chat_id, 'period', 10)
# print(users.select(chat_id, 'period'))
# users.add_reminder(chat_id, 'hello')
# print(users.select(chat_id, 'reminders'))
# users.remove_reminder(chat_id, 'Brethe!')
# print(users.select(chat_id, 'reminders'))



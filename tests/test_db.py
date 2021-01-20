import unittest
from db.users_db import Users


class TestDb(unittest.TestCase):
    """Tests of users_db"""

    @classmethod
    def setUpClass(cls):
        cls.chat_id_1 = 123456
        cls.users = Users(':memory:')
        cls.users.insert(chat_id=123456,
                         reminders=['Breathe', 'Meditate'],
                         period=60,
                         status=1,
                         active_time="10:00-20:00")
    def test_select(self):
        self.assertEqual(self.users.select(self.chat_id_1, 'reminders'), ['Breathe', 'Meditate'])
        self.assertEqual(self.users.select(self.chat_id_1, 'period'), 60)
        self.assertEqual(self.users.select(self.chat_id_1, 'status'), 1)
        self.assertEqual(self.users.select(self.chat_id_1, 'active_time'), "10:00-20:00")

    def test_update(self):
        self.users.insert(chat_id=2,
                         reminders=['Think', 'Drink'],
                         period=10,
                         status=0,
                         active_time="9:00-23:00")

        self.users.update(2, 'reminders', ['Sleep'])
        self.assertEqual(self.users.select(2, 'reminders'), ['Sleep'])

        self.users.update(2, 'period', 20)
        self.assertEqual(self.users.select(2, 'period'), 20)

        self.users.update(2, 'status', 0)
        self.assertEqual(self.users.select(2, 'status'), 0)

        self.users.update(2, 'active_time', "Actually, can store anything here. Bad practice.")
        self.assertEqual(self.users.select(2, 'active_time'), "Actually, can store anything here. Bad practice.")

    def test_add_reminder(self):
        self.users.insert(chat_id=3,
                         reminders=['First reminder'],
                          period=1000)

        self.users.add_reminder(3, 'Second reminder')
        self.assertEqual(self.users.select(3,'reminders'),  ['First reminder', 'Second reminder'])

    def test_remove_reminder(self):
        self.users.insert(chat_id=4,
                          reminders=['To stay reminder', 'Reminder to delete'],
                          period=1)

        self.users.remove_reminder(4, 'Reminder to delete')
        self.assertEqual(self.users.select(4, 'reminders'), ['To stay reminder'])


if __name__ == '__main__':
    unittest.main()

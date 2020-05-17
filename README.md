# Double pendulum simulation

To start the bot run `main.py`. In telegram bot's name is `@RandomRem_bot`

## Description
This is telegram bot that sends random messages from the given list. User can change average interval between reminders, add new ones, delete them, activate and deactivate bot. The list of all  commands can be found 

## About 
Directory `modules` consists of  3 files: 
- `bot.py` is the main one, that handles all commands and messages
- `scheduler` creates personal thread for each user that communicates with bot. This thread contains schedules for sending  messages and handles all the changes users apply via queues to the threads.
- `buttons.py` contains auxilary functions for drawing inline keyboards for some handlers.
Other directories are self explanatory.

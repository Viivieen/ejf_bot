# EJF_Vacancies Bot Setup

Follow these steps to set up and run the EJF_Vacancies bot:

## Prerequisites

1. **Create a Telegram Bot**
   - Go to [BotFather](https://t.me/botfather) on Telegram and create a bot. Note the bot token provided.
  
2. **Create a MongoDB Database**
   - Set up a MongoDB database by following this link: [MongoDB Cloud](https://cloud.mongodb.com/v2).
   - Obtain the connection string for your database.

3. **Install Python** (if not already installed)
   - Recommended version: **Python 3.10**
   - Download it from the [Python website](https://www.python.org/downloads/release/python-3100/).

4. **Install Git** (if not already installed)
   - Download Git from [Git's download page](https://git-scm.com/downloads).

## Project Setup

5. **Clone the Repository**
   - Run the following command in your terminal to clone the project locally:
     ```bash
     git clone <repository>
     ```

6. **Install Project Dependencies**
   - Navigate to the cloned project folder and run:
     ```bash
     pip install -r requirements.txt
     ```

7. **Set Up the Bot Configuration**
   - Run the following command, replacing `<database>` with your MongoDB connection string and `<bot token>` with the token from BotFather:
     ```bash
     python setup.py --database <database> --token <bot token>
     ```

## Run the Bot

8. **Start the Bot**
   - Run the following command to start the bot:
     ```bash
     python bot.py
     ```

---

This README format provides a clear, step-by-step guide for setting up and running the EJF_Vacancies bot.

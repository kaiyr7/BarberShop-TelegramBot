import telebot
import psycopg2
from telebot import types
from datetime import datetime, timedelta
import time

config = psycopg2.connect(
    host='host',
    database='database',
    user='user',
    password='password'
)
cursor = config.cursor()


bot=telebot.TeleBot('5974006996:AAEI4GJT8oXMaQyEHSu7yUnmn5JFUkhFBHA')

menu_commands = [
    telebot.types.BotCommand('start', 'Start the bot'),
    telebot.types.BotCommand('help', 'See available commands'),
    telebot.types.BotCommand('schedule', 'To get information about the schedule'),
    telebot.types.BotCommand('delete', 'To delete your registration'),
    telebot.types.BotCommand('register', 'To register for an appointment')
]
bot.set_my_commands(menu_commands)

selected_date = ""  
available_dates = []

def is_time_available(selected_date, selected_time):
    cursor.execute("SELECT COUNT(*) FROM barber WHERE date = %s AND time = %s", (selected_date, selected_time))
    count = cursor.fetchone()[0]
    return count == 0

def is_valid_phone_number(number):
    return number.isdigit() and len(number) == 11

def query_available_dates():
    today = datetime.now()
    available_dates = [today + timedelta(days=i) for i in range(3)]
    
    formatted_dates = [date.strftime("%Y-%m-%d") for date in available_dates]
    
    return formatted_dates

def is_user_registered(user_id):
    cursor.execute("SELECT * FROM barber WHERE id = %s", (user_id,))
    registration = cursor.fetchone()

    return registration

@bot.message_handler(commands=['schedule'])
def get_schedule(message):
    global available_dates 
    available_dates = query_available_dates()
    
    if available_dates:
        dates_info = "\n".join(available_dates)
        bot.send_message(message.chat.id, f"Available dates for registration:\n{dates_info}")
    else:
        bot.send_message(message.chat.id, "Sorry, there are no available dates for registration.")



@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f'Welcome, {message.from_user.first_name}, to Kaiyrzhan BarberShop')
    bot.send_message(message.chat.id, 'I am a bot for registration. Type /help to see available commands.')

@bot.message_handler(commands=['delete'])
def delete_registration(message):
    user_id = message.from_user.id

    if is_user_registered(user_id):
        cursor.execute("DELETE FROM barber WHERE id = %s", (user_id,))
        config.commit()
        bot.send_message(message.chat.id, 'Your registration has been deleted.')
    else:
        bot.send_message(message.chat.id, 'You have no registration to delete.')

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '/about - for information about the bot')
    bot.send_message(message.chat.id, '/register - to register for an appointment')

@bot.message_handler(commands=['about'])
def about(message):
    bot.send_message(message.chat.id, 'This is a bot created by Kaiyrzhan for appointments at the barbershop.')

@bot.message_handler(commands=['register'])
def register(message):
    user_id = message.from_user.id

    registration = is_user_registered(user_id)

    if registration:
        name, date, time, phonenumber = registration[1], registration[2], registration[3], registration[4]
        response_message = f'You are already registered!\nName: {name}\nDate: {date}\nTime: {time}\nPhone Number: {phonenumber}'
        bot.send_message(message.chat.id, response_message)
    else:
        global available_dates
        available_dates = query_available_dates()
        bot.reply_to(message, 'Enter your name:')
        bot.register_next_step_handler(message, get_name)

def get_name(message):
    global name
    name = message.text
    bot.reply_to(message, 'Select a date for your appointment (choose the date number):')
    
    for i, date in enumerate(available_dates):
        bot.send_message(message.chat.id, f'{i + 1}. {date}')
    
    bot.register_next_step_handler(message, get_date)

def get_date(message):
    global selected_date
    date_choice = message.text
    try:
        date_choice = int(date_choice)
        if 1 <= date_choice <= len(available_dates):
            selected_date = available_dates[date_choice - 1]
            bot.reply_to(message, 'Select the time for your appointment (from 12 to 18)')
            bot.register_next_step_handler(message, get_time)
        else:
            bot.reply_to(message, 'Please select a valid date number.')
            bot.register_next_step_handler(message, get_date)
    except ValueError:
        bot.reply_to(message, 'Please select a valid date number.')
        bot.register_next_step_handler(message, get_date)

def get_time(message):
    t = message.text
    global time
    if t.isdigit() and 12 <= int(t) <= 18:
        time = t + ':00'
        if is_time_available(selected_date, time):
            bot.reply_to(message, 'Leave your phone number')
            bot.register_next_step_handler(message, get_number)
        else:
            bot.reply_to(message, 'Sorry, the selected time is already booked. Please choose another time.')
            bot.register_next_step_handler(message, get_time)
    else:
        bot.reply_to(message, 'Please select a valid time from 12 to 18.')
        bot.register_next_step_handler(message, get_time)

def get_number(message):
    global number
    number = message.text
    if is_valid_phone_number(number):
        idy = message.from_user.id
        sql = 'INSERT INTO barber (id, name, date, time, phonenumber) VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(sql, (idy, name, selected_date, time, number))
        bot.send_message(message.chat.id, 'Registration successful')
        bot.send_message(message.chat.id, f'\nName: {name}\nDate: {selected_date}\nTime: {time}\nPhone Number: {number}')
        config.commit()
    else:
        bot.reply_to(message, 'Please enter a valid phone number.')
        bot.register_next_step_handler(message, get_number)

bot.polling(none_stop=True)

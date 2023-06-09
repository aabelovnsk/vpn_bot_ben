from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import pandas as pd
from datetime import datetime, timedelta
import os
import csv
import schedule
import time
import threading

def check_dates():
    df = pd.read_csv('users.csv')
    df['end_date'] = pd.to_datetime(df['end_date'], format="%Y-%m-%d")
    df.loc[df['end_date'] < pd.Timestamp.now(), 'access'] = 'deny'
    df.to_csv('users.csv', index=False)


# Настроим расписание
schedule.every(10).seconds.do(check_dates)

# Запустим в отдельном потоке, чтобы не блокировать основной код бота
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


threading.Thread(target=run_schedule).start()

TOKEN = '1214560409:AAEn5diTdrHgAzGvAaC0TlgPunMWdT5sdrE'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

if not os.path.exists('users.csv'):
    with open('users.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["id", "username", "user_peer", "hello_date", "start_date", "end_date", "access"])

class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.dataframe = pd.read_csv('users.csv')

    def exists(self):
        return self.user_id in self.dataframe['id'].values

    def create(self, username):
        new_user = pd.DataFrame([{
            'id': self.user_id,
            'username': username,
            'user_peer': len(self.dataframe) + 1,
            'hello_date': datetime.now().strftime("%Y-%m-%d"),
            'start_date': '',
            'end_date': '',
            'access': 'deny'
        }])
        self.dataframe = pd.concat([self.dataframe, new_user], ignore_index=True)
        self.save()

    def save(self):
        self.dataframe.to_csv('users.csv', index=False)

    def update_payment(self):
        self.dataframe.loc[self.dataframe['id'] == self.user_id, 'start_date'] = datetime.now().strftime("%Y-%m-%d")
        self.dataframe.loc[self.dataframe['id'] == self.user_id, 'end_date'] = (datetime.now() + timedelta(seconds=20)).strftime("%Y-%m-%d")
        self.dataframe.loc[self.dataframe['id'] == self.user_id, 'access'] = "accept"
        self.save()

    def access_status(self):
        return self.dataframe.loc[self.dataframe['id'] == self.user_id, 'access'].values[0]

    def get_user_peer(self):
        return self.dataframe.loc[self.dataframe['id'] == self.user_id, 'user_peer'].values[0]

class MainMenu:
    @staticmethod
    async def show(user_id):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton('Данные для подключения'), KeyboardButton('Инструкция'), KeyboardButton('Проверить доступ'), KeyboardButton('Продлить доступ'))
        await bot.send_message(chat_id=user_id, text="Что вы хотите:", reply_markup=keyboard)

class StartMenu:
    @staticmethod
    async def show(user_id):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton('Да'), KeyboardButton('Нет'))
        await bot.send_message(chat_id=user_id, text="Хотите купить VPN?", reply_markup=keyboard)

class ConnectionData:
    @staticmethod
    async def send(user_id, user_peer):
        await bot.send_document(chat_id=user_id, document=open(f'/home/bennyhils/wirehole/wireguard/peer{user_peer}/peer{user_peer}.conf', 'rb'))
        await bot.send_photo(chat_id=user_id, photo=open(f'/home/bennyhils/wirehole/wireguard/peer{user_peer}/peer{user_peer}.png', 'rb'))

class Instructions:
    @staticmethod
    async def send(user_id):
        await bot.send_document(chat_id=user_id, document=open('/home/aabelov/manual.txt', 'rb'))

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user = User(user_id=message.from_user.id)
    if user.exists():
        await MainMenu.show(user_id=message.from_user.id)
    else:
        user.create(username=message.from_user.username)
        await StartMenu.show(user_id=message.from_user.id)

@dp.message_handler(lambda message: message.text == 'Да')
async def buy(message: types.Message):
    user = User(user_id=message.from_user.id)
    # Process payment with Bank 131 here
    # If payment is successful:
    user.update_payment()
    await MainMenu.show(user_id=message.from_user.id)

@dp.message_handler(lambda message: message.text == 'Данные для подключения')
async def send_connection_data(message: types.Message):
    user = User(user_id=message.from_user.id)
    if user.access_status() == 'deny':
        await message.reply("Доступ зарещен, проверьте с помощью кнопки 'Проверить доступ'")
        await MainMenu.show(user_id=message.from_user.id)
    else:
        await ConnectionData.send(user_id=message.from_user.id, user_peer=user.get_user_peer())
        await MainMenu.show(user_id=message.from_user.id)

@dp.message_handler(lambda message: message.text == 'Инструкция')
async def send_instructions(message: types.Message):
    await Instructions.send(user_id=message.from_user.id)
    await MainMenu.show(user_id=message.from_user.id)

@dp.message_handler(lambda message: message.text == 'Проверить доступ')
async def check_access(message: types.Message):
    user = User(user_id=message.from_user.id)
    if user.access_status() == 'deny':
        await message.reply("Необходимо оплатить доступ к VPN")
    else:
        await message.reply("Доступ предоставлен")
    await MainMenu.show(user_id=message.from_user.id)

@dp.message_handler(lambda message: message.text == 'Продлить доступ')
async def extend(message: types.Message):
    user = User(user_id=message.from_user.id)
    # Process payment with Bank 131 here
    # If payment is successful:
    user.update_payment()
    await MainMenu.show(user_id=message.from_user.id)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
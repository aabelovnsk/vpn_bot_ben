from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import pandas as pd
from datetime import datetime, timedelta
import os
import csv

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
            'hello_date': datetime.now().strftime("%d:%m:%Y"),
            'start_date': '',
            'end_date': '',
            'access': 'deny'
        }])
        self.dataframe = pd.concat([self.dataframe, new_user], ignore_index=True)
        self.save()

    def save(self):
        self.dataframe.to_csv('users.csv', index=False)

    def update_payment(self):
        self.dataframe.loc[self.dataframe['id'] == self.user_id, 'start_date'] = datetime.now().strftime("%d:%m:%Y")
        self.dataframe.loc[self.dataframe['id'] == self.user_id, 'end_date'] = (datetime.now() + timedelta(days=30)).strftime("%d:%m:%Y")
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
        keyboard.add(KeyboardButton('Connection Data'), KeyboardButton('Instructions'), KeyboardButton('Check Access'), KeyboardButton('Extend'))
        await bot.send_message(chat_id=user_id, text="Choose an option:", reply_markup=keyboard)

class StartMenu:
    @staticmethod
    async def show(user_id):
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton('Buy'), KeyboardButton('No'))
        await bot.send_message(chat_id=user_id, text="Brother, do you need a VPN?", reply_markup=keyboard)

class ConnectionData:
    @staticmethod
    async def send(user_id, user_peer):
        await bot.send_document(chat_id=user_id, document=open(f'/home/bennyhils/wirehole/wirefuard/peer{user_peer}/peer{user_peer}.conf', 'rb'))
        await bot.send_photo(chat_id=user_id, photo=open(f'/home/bennyhils/wirehole/wirefuard/peer{user_peer}/peer{user_peer}.png', 'rb'))

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

@dp.message_handler(lambda message: message.text == 'Buy')
async def buy(message: types.Message):
    user = User(user_id=message.from_user.id)
    # Process payment with Bank 131 here
    # If payment is successful:
    user.update_payment()
    await MainMenu.show(user_id=message.from_user.id)

@dp.message_handler(lambda message: message.text == 'Connection Data')
async def send_connection_data(message: types.Message):
    user = User(user_id=message.from_user.id)
    if user.access_status() == 'deny':
        await message.reply("Access is denied, press the 'Check Access' button")
        await MainMenu.show(user_id=message.from_user.id)
    else:
        await ConnectionData.send(user_id=message.from_user.id, user_peer=user.get_user_peer())
        await MainMenu.show(user_id=message.from_user.id)

@dp.message_handler(lambda message: message.text == 'Instructions')
async def send_instructions(message: types.Message):
    await Instructions.send(user_id=message.from_user.id)
    await MainMenu.show(user_id=message.from_user.id)

@dp.message_handler(lambda message: message.text == 'Check Access')
async def check_access(message: types.Message):
    user = User(user_id=message.from_user.id)
    if user.access_status() == 'deny':
        await message.reply("Paid period has expired")
    else:
        await message.reply("Access is granted")
    await MainMenu.show(user_id=message.from_user.id)

@dp.message_handler(lambda message: message.text == 'Extend')
async def extend(message: types.Message):
    user = User(user_id=message.from_user.id)
    # Process payment with Bank 131 here
    # If payment is successful:
    user.update_payment()
    await MainMenu.show(user_id=message.from_user.id)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
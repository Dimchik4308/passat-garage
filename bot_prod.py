import asyncio
import logging
import uvicorn
import sys
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, CallbackQuery
from aiogram.types.web_app_info import WebAppInfo
from aiogram.types import FSInputFile,InputMediaPhoto
from app import app as flaskapp
from shared.database import db
from shared.models import Good,BotUser,Order, BotLogin
import os
from dotenv import load_dotenv

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
load_dotenv()

bot=Bot(token=os.getenv("BOT_TOKEN"))
dp=Dispatcher()
markup=ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text='🌐 Наш сайт',web_app=WebAppInfo(url=BASE_URL))
        ],
        [
            KeyboardButton(text='🛒 Каталог товарів')
        ]

    ],
    resize_keyboard=True,
    input_field_placeholder='Оберіть що вам потрібно...'
)

codes={}
logging.basicConfig(level=logging.INFO, stream=sys.stdout)


@dp.message(CommandStart())
async def start(message :types.Message):
    telegram_id = message.from_user.id
    with flaskapp.app_context():
        if not db.session.query(BotUser).filter_by(user_telegram_id=telegram_id).first():
            db.session.add(BotUser(user_telegram_id=telegram_id))
            db.session.commit()
    await message.answer(f'Привіт, {message.from_user.first_name}. Що тебе цікавить?',reply_markup=markup)

def get_product(page_index:int):
    with flaskapp.app_context():
        total_goods=db.session.query(Good).count()
        good=db.session.query(Good).offset(page_index).limit(1).first()
    price_text='Задарма' if good.price==0 else f'{good.price}₴'
    text = (
        f' 🚗{good.title}🚗\n'
        f'💲 Ціна: {price_text}\n'
        f'🛒 Купити: <a href="{BASE_URL}/catalog/{good.slug}">{good.title}</a>'
    )
    buttons=[]
    if page_index>0:
        buttons.append(InlineKeyboardButton(text='⬅️', callback_data=f'page_{page_index - 1}'))
    if page_index<total_goods-1:
        buttons.append(InlineKeyboardButton(text='➡️', callback_data=f'page_{page_index + 1}'))

    keyboard=InlineKeyboardMarkup(inline_keyboard=[buttons])
    return good.image_url,text,keyboard

@dp.message(F.text == '🛒 Каталог товарів')
async def start_catalog(message: types.Message):
    image_url,text,keyboard=get_product(page_index=0)
    photo=FSInputFile(image_url)
    await message.answer_photo(photo=photo,caption=text,reply_markup=keyboard,parse_mode='HTML')


@dp.callback_query(F.data.startswith('page_'))
async def flip(call: types.CallbackQuery):
    new_page=int(call.data.split('_')[1])
    image_url, text, keyboard = get_product(page_index=new_page)
    photo=FSInputFile(image_url)
    media=InputMediaPhoto(media=photo,caption=text,parse_mode='HTML')
    await call.message.edit_media(media=media,reply_markup=keyboard)
    await call.answer()


app = FastAPI()

class GoodNot (BaseModel):
    img_url:str
    title: str
    price: int
    slug: str
    seller:str

class OrderNot (BaseModel):
    fname:str
    sname: str
    quantity: int
    town: str
    mail:str
    zip_code:str
    comment:str
    seller_id:str
    good_title:str
    total:int
    email:str


async def broadcast_message(user_ids: list[int], text: str, img_path: str):
    photo = None
    if img_path:
        try:
            photo = FSInputFile(img_path)
        except Exception:
            pass

    for user_id in user_ids:
        try:
            if photo:
                await bot.send_photo(chat_id=user_id, photo=photo, caption=text, parse_mode="HTML")
            else:
                await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"⚠️ Не доставлено {user_id}: {e}")

class Status(BaseModel):
    code:str
    title:str
    seller_id:int
    buyer_id:int
    seller_email:str
    buyer_email:str
    seller_name:str
    buyer_name:str

@app.post('/api/order_status')
async def send_status(status: Status):
    if status.code=='denied':
        text=(f'🚨Продавець {status.seller_name}🚨'
              f'❎ Відхилив ваше замовлення {status.title} ❎'
              f'✉️ Написати продавцю <a href="mailto:{status.seller_email}">{status.seller_email}</a>'
              )
        with flaskapp.app_context():
            tg = BotLogin.query.filter_by(user_id=status.buyer_id).first()
        await bot.send_message(chat_id=tg.user_telegram_id, text=text, parse_mode="HTML")
    if status.code == 'inprocess':
        text = (f'🚨 Продавець {status.seller_name} 🚨'
                f'✅ Підтвердив ваше замовлення {status.title} ✅'
                f'😉 Ваше замовлення вже в обробці 😉'
                )
        with flaskapp.app_context():
            tg = BotLogin.query.filter_by(user_id=status.buyer_id).first()
        await bot.send_message(chat_id=tg.user_telegram_id, text=text, parse_mode="HTML")
    if status.code == 'finished':
        text = (f'🚨 Покупець {status.buyer_name} 🚨'
                f'✅ Забрав замовлення {status.title} з пошти ✅'
                f'💲 Очікуйте поступлення оплати 💲'
                )
        with flaskapp.app_context():
            tg = BotLogin.query.filter_by(user_id=status.seller_id).first()
        await bot.send_message(chat_id=tg.user_telegram_id, text=text, parse_mode="HTML")


@app.post('/api/order_not')
async def send_order_info(order:OrderNot):
    text=(f"🚨 У вас нове замовлення 🚨\n"
          f"👤 Ім'я покупця: {order.fname}\n"
          f"👤 Прізвище покупця: {order.sname}\n"
          f'🛒 Товар: {order.good_title}\n'
          f'📍 Місто: {order.town}\n'
          f'✉️ Пошта: {order.mail}\n'
          f'📫 Індекс: {order.zip_code}\n'
          f'💬 Коментар: {order.comment}\n'
          f'🔢 Кількість: {order.quantity}\n'
          f"💲 Сума: {order.total}\n"
          f'<a href="mailto:{order.email}">📩 {order.email}</a>')
    with flaskapp.app_context():
        tg=BotLogin.query.filter_by(user_id=order.seller_id).first()
    await bot.send_message(chat_id=tg.user_telegram_id,text=text,parse_mode="HTML")

@app.post('/api/notify')
async def send_not(good: GoodNot, background_tasks: BackgroundTasks):
    price_text = 'Задарма' if good.price == 0 else f'{good.price}₴'
    text = (
        f'🚨 Новий товар на сайті \n'
        f'🚗{good.title}🚗\n'
        f'💲 Ціна: {price_text}\n'
        f'👤 Продавець: {good.seller}\n'
        f'🛒 Купити: <a href="{BASE_URL}/catalog/{good.slug}">{good.title}</a>'
    )
    user_ids = []
    with flaskapp.app_context():
        users = db.session.query(BotUser).all()
        user_ids = [u.user_telegram_id for u in users]
    if user_ids:
        background_tasks.add_task(broadcast_message, user_ids, text, good.img_url)
    return {"status": "ok", "message": "Повідомлення успішно відправлено в ТГ!"}

class Link(BaseModel):
    code: int
    us_id: int

@app.post('/api/link')
async def link(data: Link):
    global codes
    code=data.code
    us=data.us_id
    codes[code]=us
    print(codes)
    return {"status": "ok", "message": "Код очікує активації в боті"}

@dp.message(Command('link'))
async def link(message: types.Message, command: CommandObject):
    global codes
    if command.args is None:
        await message.answer('Введіть код після команди')
        return
    try:
        code=int(command.args)
        print(code,codes)
    except ValueError:
        await message.answer('Код має складатися лише з цифр')
        return
    if code in codes:
        user_id=codes[code]
        tg_id=message.from_user.id
        try:
            with flaskapp.app_context():
                tg_user=BotLogin(user_id=user_id,user_telegram_id=tg_id)
                db.session.add(tg_user)
                db.session.commit()
            await message.answer("Ви успішно прив'язали телеграм до вашого акаунту")
            del codes[code]
        except Exception as e:
            await message.answer('Виникла помилка, спробуйте ще раз')
            del codes[code]
    else:
        await message.answer('Ваш код неправильний')


async def main():
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)

    await bot.delete_webhook(drop_pending_updates=True)

    logging.info("🚀 Запускаю API і Бота разом...")

    await asyncio.gather(
        dp.start_polling(bot),
        server.serve()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Зупинка...")

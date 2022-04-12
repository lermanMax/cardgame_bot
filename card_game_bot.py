import asyncio
import logging
import typing

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import callback_data, exceptions
import random

from fileDB_for_id import put_id_in_file, get_id, get_text_from
from config import API_TOKEN, DB_SUBSCRIBERS

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('messages_sender')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

vote_cb = callback_data.CallbackData('vote', 'action')  # vote:<action>

get_card_word = '⚙️ 📊 🛒 Взять карту'
delete_card_word = '🗑️ Сбросить'
delete_card_action = 'delete_message'

basemenu_list = [get_card_word, ]

card_photo_cache = {}  # {number: tg_file_id}

last_card_cache = {}  # {user_id: number, ...}

market_numbers_range = (1, 29)
market_number_sequence = [
    n for n in range(market_numbers_range[0], market_numbers_range[1]+1)]
tech_numbers_range = (30, 55)
tech_number_sequence = [
    n for n in range(tech_numbers_range[0], tech_numbers_range[1]+1)]
trend_numbers_range = (56, 87)
trend_number_sequence = [
    n for n in range(trend_numbers_range[0], trend_numbers_range[1]+1)]


async def send_message(
        user_id: int,
        text: str,
        disable_notification: bool = False) -> bool:
    """
    Safe messages sender
    :param user_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        await bot.send_message(
            user_id,
            text,
            disable_notification=disable_notification)
    except exceptions.BotBlocked:
        log.error(f"Target [ID:{user_id}]: blocked by user")
    except exceptions.ChatNotFound:
        log.error(f"Target [ID:{user_id}]: invalid user ID")
    except exceptions.RetryAfter as e:
        log.error(
            f"Target [ID:{user_id}]: Flood limit is exceeded."
            f"Sleep {e.timeout} seconds.")
        await asyncio.sleep(e.timeout)
        return await send_message(user_id, text)  # Recursive call
    except exceptions.UserDeactivated:
        log.error(f"Target [ID:{user_id}]: user is deactivated")
    except exceptions.TelegramAPIError:
        log.exception(f"Target [ID:{user_id}]: failed")
    else:
        log.info(f"Target [ID:{user_id}]: success")
        return True
    return False


async def send_to_everybody(text):
    count = 0
    try:
        for user_id in get_id(DB_SUBSCRIBERS):
            if await send_message(user_id, text):
                count += 1
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30)
    finally:
        log.info(f"{count} messages successful sent.")

    return count


def get_card_keyboard():
    """ Возвращает клавиатуру для карточки """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton(
            delete_card_word,
            callback_data=vote_cb.new(action=delete_card_action)))
    return keyboard


def get_basemenu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in basemenu_list:
        keyboard.add(types.KeyboardButton(name))
    return keyboard


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    logging.info('start command from: %r', message.from_user.id)
    result = put_id_in_file(message.from_user.id, DB_SUBSCRIBERS)
    logging.info('result of putting id in file: %r', result)
    text = get_text_from('./text_of_questions/first_instruction.txt')
    keyboard = get_basemenu_keyboard()
    await message.answer(text, reply_markup=keyboard)
    await send_help(message)


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    logging.info('help command from: %r', message.from_user.id)
    keyboard = get_basemenu_keyboard()
    await message.answer(
        get_text_from('./text_of_questions/help.txt'),
        reply_markup=keyboard
    )


@dp.callback_query_handler(vote_cb.filter(
        action=[delete_card_action, ]))
async def callback_vote_action(
        query: types.CallbackQuery, callback_data: typing.Dict[str, str]):

    # callback_data contains all info from callback data
    logging.info('Got this callback data: %r', callback_data)

    await query.answer()  # answer callback query as soon as possible
    callback_data_action = callback_data['action']

    if callback_data_action == delete_card_action:
        await bot.delete_message(
            chat_id=query.from_user.id,
            message_id=query.message.message_id
        )
        logging.info('Delete card')
    else:
        logging.info('Unkown callback_data: %r', callback_data)


def get_card_number_for_user(user_id: int) -> int:
    if user_id not in last_card_cache:
        return random.choice(
            market_number_sequence
            + tech_number_sequence
            + trend_number_sequence
        )
    last_naumber = last_card_cache[user_id]
    if last_naumber in market_number_sequence:
        return random.choice(tech_number_sequence + trend_number_sequence)

    elif last_naumber in tech_number_sequence:
        return random.choice(market_number_sequence + trend_number_sequence)

    elif last_naumber in trend_number_sequence:
        return random.choice(market_number_sequence + tech_number_sequence)

    else:
        logging.info('number out of range')
        return 1


async def send_photo_and_save_id(card_number: int, message: types.Message):
    card = types.InputFile(f"./cards/{ card_number }.png")
    sended_msg = await bot.send_photo(
        chat_id=message.chat.id,
        photo=card,
        reply_markup=get_card_keyboard()
    )
    card_photo_cache[card_number] = sended_msg.photo[0].file_id


@dp.message_handler(lambda message: message.text in basemenu_list)
async def base_menu(message: types.Message):
    """
    Получаем нажатие кнопки из базового меню
    """
    logging.info('push basemenu button from: %r', message.from_user.id)
    if message.text == get_card_word:
        card_number = get_card_number_for_user(message.from_user.id)
        if card_number in card_photo_cache:
            card = card_photo_cache[card_number]
            try:
                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=card,
                    reply_markup=get_card_keyboard()
                )
            except exceptions.WrongFileIdentifier:
                logging.error(f'wrong file ID for card number: {card_number}')
                await send_photo_and_save_id(card_number, message)
        else:
            await send_photo_and_save_id(card_number, message)

        last_card_cache[message.from_user.id] = card_number
    return


@dp.message_handler(commands=['all'])
async def cache_all_photo_command(message: types.Message):
    logging.info('push admin comand "all" from: %r', message.from_user.id)
    full_seq = (
        market_number_sequence
        + tech_number_sequence
        + trend_number_sequence
    )
    for n in full_seq:
        card = types.InputFile(f"./cards/{ n }.png")
        sended_msg = await bot.send_photo(
            chat_id=message.chat.id,
            photo=card,
            reply_markup=get_card_keyboard()
        )
        card_photo_cache[n] = sended_msg.photo[0].file_id


@dp.message_handler(content_types=types.message.ContentType.ANY)
async def staf(message: types.Message):
    """ любой другой контент просто отметаем"""
    logging.info('strange staf from: %r', message.from_user.id)
    await message.reply(
        get_text_from('./text_of_questions/wtf.txt'),
        reply_markup=get_basemenu_keyboard()
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
)

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
API_URL = 'https://praktikum.yandex.ru/api/user_api/{}'
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def parse_homework_status(homework: dict) -> str:
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_name is None or homework_status is None:
        message = 'Не удалось получить данные.'
        logging.error(message)
        return message

    if homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework_status == 'approved':
        verdict = ('Ревьюеру всё понравилось, можно '
                   'приступать к следующему уроку.')
    elif homework_status == 'reviewing':
        verdict = 'Работа взята в ревью.'
    else:
        message = (f'У работы "{homework_name}" неизвестный '
                   f'статус: {homework_status}.')
        logging.error(message)
        return message

    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp: int) -> dict:
    params = {'from_date': current_timestamp, }
    headers = {'Authorization': 'OAuth ' + PRAKTIKUM_TOKEN, }

    try:
        api_url = API_URL.format('homework_statuses/')
        homework_statuses = requests.get(api_url, params, headers=headers)
        return homework_statuses.json()

    except Exception as e:
        message = f'Не удалось получить данные. Возникла ошибка: {e}.'
        logging.error(message)

    return {}


def send_message(message: str, bot_client):
    logging.info('Сообщение отправлено')
    return bot_client.send_message(CHAT_ID, message)


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Бот запущен.')
    timestamp = int(time.time())

    while True:
        try:
            homework_statuses = get_homework_statuses(timestamp)
            homeworks = homework_statuses.get('homeworks')
            if homeworks:
                send_message(parse_homework_status(homeworks[0]), bot)
            timestamp = homework_statuses.get('current_date', int(time.time()))
            time.sleep(30)

        except Exception as e:
            message = f'Бот столкнулся с ошибкой: {e}'
            logging.error(message)
            send_message(message, bot)
            time.sleep(60)


if __name__ == '__main__':
    main()

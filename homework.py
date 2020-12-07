import logging
import os
import time

import requests
from requests.exceptions import HTTPError
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
POLL_DICT = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
}
MY_WARNING = 'Произошла ошибка при запросе через API, текст ошибки: '
BOT_ERROR_TEXT = f'Бот столкнулся с ошибкой:'
LOGGER = logging.getLogger('myLogger')


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework.get('status') in POLL_DICT.keys():
        return f'У вас проверили работу "{homework_name}"!\n' \
               f'\n{POLL_DICT[homework.get("status")]}'
    return f'{MY_WARNING}{homework.get("error")}'


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            PRAKTIKUM_URL,
            headers=HEADERS,
            params=params
        )
    except HTTPError as http_err:
        LOGGER.error(f'Ошибка при обработке запроса: {http_err}'
                     f'Параметры запроса: '
                     f'headers = {HEADERS}'
                     f'params = {params}')

    else:
        return response.json()


def send_message(message, bot_client=telegram.Bot(token=TELEGRAM_TOKEN)):
    return bot_client.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                text = parse_homework_status(new_homework.get('homeworks')[0])
                send_message(text)
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(1200)
        except Exception as e:
            LOGGER.error(f'{BOT_ERROR_TEXT} {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()

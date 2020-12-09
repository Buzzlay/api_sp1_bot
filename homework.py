import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
REACTIONS = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.'
}
MY_WARNING = 'Произошла ошибка при запросе через API, ' \
             'неожиданный статус домашнего задания: "{status}"'
BOT_ERROR_TEXT = 'Бот столкнулся с ошибкой: {exception}'
BOT_ANSWER = 'У вас проверили работу "{name}"!\n' \
             '\n{reaction}'
CONNECTION_ERROR = ('Ошибка при отправке запроса: {error}\n'
                    'URL запроса: {url}\n'
                    'Параметры запроса:\n'
                    'headers = {headers}\n'
                    'params = {params}\n')
PROCESSING_ERROR = ('Возникла ошибка при обработке запроса сервером,\n'
                    'Текст ошибки: "{error}"')
logger = logging.getLogger('myLogger')


def parse_homework_status(homework):
    name = homework.get('homework_name')
    status = homework['status']
    if status in REACTIONS:
        reaction = REACTIONS[status]
        return BOT_ANSWER.format(
            name=name,
            reaction=reaction
        )
    raise MY_WARNING.format(status=status)


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            PRAKTIKUM_URL,
            headers=HEADERS,
            params=params
        )
    except requests.exceptions.RequestException as error:
        raise ConnectionError(CONNECTION_ERROR.format(
            error,
            PRAKTIKUM_URL,
            HEADERS,
            params
        ))
    else:
        if 'error' in response.json():
            raise IOError(PROCESSING_ERROR.format(error=response.json()['error']))
        else:
            return response.json()


def send_message(message, bot_client=None):
    bot_client = telegram.Bot(
        token=TELEGRAM_TOKEN
    ) if bot_client is None else bot_client
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
        except Exception as exception:
            logger.error(BOT_ERROR_TEXT.format(exception=exception))
            time.sleep(5)


if __name__ == '__main__':
    main()

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
REACTIONS = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.',
    'reviewing': 'Ревьюер начал проверять работу'
}
MY_WARNING = 'Произошла ошибка при запросе через API, ' \
             'неожиданный статус домашнего задания: "{status}"'
BOT_ERROR_TEXT = 'Бот столкнулся с ошибкой: {exception}'
BOT_ANSWER = 'У вас проверили работу "{name}"!\n' \
             '\n{reaction}\n' \
             'Комментарий ревьюера: {comment}'
CONNECTION_ERROR = ('Ошибка при отправке запроса: {error}\n'
                    'URL запроса: {url}\n'
                    'Параметры запроса:\n'
                    'headers = {headers}\n'
                    'params = {params}\n')
PROCESSING_ERROR = ('Возникла ошибка при обработке запроса сервером,\n'
                    'Текст ошибки: "{error}"\n'
                    'URL запроса: {url}\n'
                    'Код ответа: {status_code}\n'
                    'Параметры запроса:\n'
                    'headers = {headers}\n'
                    'params = {params}\n')
logger = logging.getLogger('myLogger')


def parse_homework_status(homework):
    name = homework.get('homework_name')
    status = homework['status']
    comment = homework['reviewer_comment']
    if status not in REACTIONS:
        raise ValueError(MY_WARNING.format(status=status))
    reaction = REACTIONS[status]
    return BOT_ANSWER.format(
        name=name,
        reaction=reaction,
        comment=comment
    )


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            url=PRAKTIKUM_URL,
            headers=HEADERS,
            params=params
        )
    except requests.exceptions.RequestException as error:
        raise ConnectionError(CONNECTION_ERROR.format(
            error=error,
            url=PRAKTIKUM_URL,
            headers=HEADERS,
            params=params
        ))
    response_data = response.json()
    error_keys = ['error', 'code']
    for item in error_keys:
        if item in response_data:
            raise HTTPError(PROCESSING_ERROR.format(
                error=response_data[item],
                url=PRAKTIKUM_URL,
                status_code=response.status_code,
                headers=HEADERS,
                params=params
            ))
    return response_data


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

import os
import time
import sys

import requests
import telegram

from dotenv import load_dotenv


load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ENVIRONMENT = os.getenv('ENVIRONMENT')


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(session, current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    params = {'from_date': 0}
    try:
        homework_statuses = session.get(
            url,
            headers=headers,
            params=params
        )
        homework_statuses.raise_for_status()

    except requests.HTTPError as http_err:
        bot_interrupt(http_err)
    except requests.RequestException:
        return {}

    return homework_statuses.json()


def send_message(bot, message):
    
    return bot.send_message(
        chat_id=CHAT_ID, 
        text=message,
        connection_timeout=10,
        read_timeout=10
    )


def bot_interrupt(err_message):
    response = f'Работа бота остановлена. Ошибка: {err_message}'
    print(response)
    sys.exit(1)


def main():
    current_timestamp = int(time.time())

    if ENVIRONMENT == 'dev':
        proxy_url = 'socks5://134.209.100.103:49616'
        proxy = telegram.utils.request.Request(proxy_url=proxy_url)
        bot = telegram.Bot(token=TELEGRAM_TOKEN, request=proxy)
    elif ENVIRONMENT == 'prod':
        bot = telegram.Bot(token=TELEGRAM_TOKEN)

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=10)
    session.mount('https://', adapter)

    while True:

        try:
            new_homework = get_homework_statuses(session, current_timestamp)
            if new_homework.get('homeworks'):
                send_message(bot, parse_homework_status(new_homework.get('homeworks')[0]))
            current_timestamp = new_homework.get('current_date')
            time.sleep(900)

        except Exception as e:
            bot_interrupt(e)


if __name__ == '__main__':
    main()

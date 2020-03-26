import os
import time

import requests
import telegram

from dotenv import load_dotenv


load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

proxy_url = 'socks5://134.209.100.103:49616'
proxy = telegram.utils.request.Request(proxy_url=proxy_url)
bot = telegram.Bot(token=TELEGRAM_TOKEN, request=proxy)


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    params = {'from_date': current_timestamp}

    try:
        homework_statuses = requests.get(
            url,
            headers=headers,
            params=params
        )
    
    except requests.exceptions.RequestException as e:
        raise bot_interrupt(e)
    
    if homework_statuses.json().get('source'):
        e = homework_statuses.json().get('message')
        raise bot_interrupt(e)

    return homework_statuses.json()


def send_message(message):

    return bot.send_message(
        chat_id=CHAT_ID, 
        text=message,
        connection_timeout=10,
        read_timeout=10
    )


def bot_interrupt(e):
    response = f'Работа бота остановлена. Ошибка: {e}'
    return SystemExit(response)


def main():
    current_timestamp = int(time.time())

    while True:
        
        try:
            all_homeworks = get_homework_statuses(current_timestamp)
            new_homework = all_homeworks.get('homeworks')[0]
            if new_homework:
                send_message(parse_homework_status(new_homework))
            current_timestamp = new_homework.get('current_date')
            time.sleep(300)

        except Exception as e:
            raise bot_interrupt(e)


if __name__ == '__main__':
    main()

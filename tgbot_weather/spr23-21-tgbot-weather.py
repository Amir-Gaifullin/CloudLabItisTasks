"""Telegram Bot on Yandex Cloud Function."""
import os
import json
import requests
import datetime
import configparser
import boto3
from zoneinfo import ZoneInfo

# Этот словарь будем возвращать, как результат функции.
FUNC_RESPONSE = {
    'statusCode': 200,
    'body': ''
}
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
API_KEY = os.environ['API_KEY']
API_KEY_VOICE = os.environ['API_KEY_VOICE']
AUTH_HEADER = f"Api-Key {API_KEY}"
AUTH_HEADER_VOICE = f"Api-Key {API_KEY_VOICE}"
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

# Базовая часть URL для доступа к Telegram Bot API.
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def degToCompass(num):
    val=int((num/11.25)+.5)
    arr=["С","ССВ","СВ","ВСВ","В","ВЮВ", "ЮВ", "ЮЮВ","Ю","ЮЮЗ","ЮЗ","ЗЮЗ","З","ЗСЗ","СЗ","ССЗ"]
    return arr[(val % 8)]


def convertUnixToTime(unix):
  date_time = datetime.datetime.fromtimestamp(unix)
  utc = ZoneInfo('UTC')
  moslowtz = ZoneInfo('Europe/Moscow')
  date_time = date_time.replace(tzinfo=utc)
  moskowtime = date_time.astimezone(moslowtz)
 
  return moskowtime.strftime('%H:%M')
  

def get_weather_from_text(city_name):
  city = city_name
  lang = 'ru'
  token = '890dbe39dd1ea4041d77acb119367474'
  param = {'q': city, 'appid': token, 'lang': lang, 'units': 'metric'}
  url = 'http://api.openweathermap.org/data/2.5/weather'
  response = requests.get(url, params=param)
  if response.status_code == 200:
      data = response.json()
      return data
  else:
      return None

def get_weather_from_location(location):
  lang = 'ru'
  token = '890dbe39dd1ea4041d77acb119367474'
  param = {'lat': location['latitude'], 'lon': location['longitude'], 'appid': token, 'lang': lang, 'units': 'metric'}
  url = 'http://api.openweathermap.org/data/2.5/weather'
  response = requests.get(url, params=param)
  if response.status_code == 200:
      data = response.json()
      return data
  else:
      return None

def get_file(file_id):
    resp = requests.post(url=f'{TELEGRAM_API_URL}/getFile', json={'file_id': file_id})
    return resp.json()['result']


def send_message(text, message):
    """Отправка сообщения пользователю Telegram."""

    # Формируем данные для метода sendMessage из Telegram Bot API
    message_id = message['message_id']
    chat_id = message['chat']['id']
    reply_message = {'chat_id': chat_id,
                     'text': text,
                     'reply_to_message_id': message_id}

    # POST запросом отправим данные на сервер Telegram Bot API
    # Объект будет преобразован в JSON и отправиться как тело HTTP запроса.
    requests.post(url=f'{TELEGRAM_API_URL}/sendMessage', json=reply_message)

def send_voice(voice_file, message):
    """Отправка сообщения пользователю Telegram."""

    # Формируем данные для метода sendMessage из Telegram Bot API
    voice_path = f"https://storage.yandexcloud.net/itiscl-spr23-21-public/{voice_file}"
    message_id = message['message_id']
    chat_id = message['chat']['id']
    reply_message = {'chat_id': chat_id,
                     'voice': voice_path,
                     'reply_to_message_id': message_id}

    # POST запросом отправим данные на сервер Telegram Bot API
    # Объект будет преобразован в JSON и отправиться как тело HTTP запроса.
    requests.post(url=f'{TELEGRAM_API_URL}/sendVoice', json=reply_message)


def handler(event, context):
    """Обработчик облачной функции. Реализует Webhook для Telegram Bot."""

    # Наличие токена Telegram Bot обязательно, поэтому если он не
    # определен среди переменных окружения, то завершим облачную функцию с
    # кодом 200, что бы сервер Telegram Bot API повторно не отправлял на
    # обработку это сообщение.
    if TELEGRAM_BOT_TOKEN is None:
        return FUNC_RESPONSE

    # Среда выполнения в аргументе event передает данные об HTTP запросе
    # преобразованные в словарь. В этом словаре по ключу body содержится тело
    # HTTP запроса. Сервер Telegram Bot API при использовании Webhook передает
    # в теле HTTP запроса объект Update в JSON формате. Мы этот объект
    # преобразуем в словарь.
    update = json.loads(event['body'])
    

    # В объекте Update должно быть поле message содержащее объект Message
    # (сообщение пользователя). Если его нет, то завершим облачную функцию с
    # кодом 200, что бы сервер Telegram Bot API повторно не отправлял на
    # обработку это сообщение.
    if 'message' not in update:
        return FUNC_RESPONSE

    # Если поле message присутствует, то извлекаем объект Message.
    message_in = update['message']

    # Так как обрабатываем только текстовые сообщения, поэтому проверяем есть ли
    # поле text в полученном сообщении. Если текстового сообщения нет, то
    # отправим пользователю предупреждение и завершим облачную функцию с кодом
    # 200, что бы сервер Telegram Bot API повторно не отправлял на обработку это
    # сообщение.
      

    if 'text' in message_in:
        if '/help' in message_in['text']:
            send_message("""
            \n
            Я могу ответить на:
            - Текстовое сообщение с названием населенного пункта.
            - Голосовое сообщение с названием населенного пункта.
            - Сообщение с точкой на карте.""",
                      message_in)
            return FUNC_RESPONSE

        if '/start' in message_in['text']:
            send_message('Я сообщу вам о погоде в том месте, которое сообщите мне.', message_in)
            return FUNC_RESPONSE

        weather_data = get_weather_from_text(message_in['text'])

        if weather_data == None:
            result = f"Я не нашел населенный пункт {message_in['text']}."
        else:
            result = f"{weather_data['weather'][0]['description']}.\nТемпература {weather_data['main']['temp']} ℃, ощущается как {weather_data['main']['feels_like']} ℃.\nАтмосферное давление {weather_data['main']['pressure']} мм рт. ст.\nВлажность {weather_data['main']['humidity']} %.\nВидимость {weather_data['visibility']} метров.\nВетер {weather_data['wind']['speed']} м/с, направление ветра {degToCompass(weather_data['wind']['deg'])}.\nВосход солнца {convertUnixToTime(weather_data['sys']['sunrise'])} МСК. Закат {convertUnixToTime(weather_data['sys']['sunset'])} МСК.\n"

        send_message(result, message_in)
        return FUNC_RESPONSE

    if 'voice' in message_in:
        voice = message_in['voice']
        duration = voice['duration']

        if duration > 30:
            send_message('Я не могу понять голосовое сообщение длительность более 30 секунд.', message_in)
            return FUNC_RESPONSE

        file_id = voice['file_id']
        tg_file = get_file(file_id)
        tg_file_path = tg_file['file_path']

        file_resp = requests.get(url=f'https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{tg_file_path}')
        audio = file_resp.content

        stt_resp = requests.post(url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize",
                                 headers = {'Authorization': AUTH_HEADER},
                                 data = audio)
        if stt_resp.ok:
            city = stt_resp.json()['result']
            
            weather_data = get_weather_from_text(city)
            if weather_data == None:
                result = f"Я не нашел населенный пункт {city}."
            else:
                temp = int(weather_data['main']['temp'])
                feels_like_temp = int(weather_data['main']['feels_like'])
                result = f"Населенный пункт {weather_data['name']}.\n{weather_data['weather'][0]['description']}.\nТемпература {temp}.\n Ощущается как {feels_like_temp}.\nДавление {weather_data['main']['pressure']}.\nВлажность {weather_data['main']['humidity']}."
        else:
            send_message("Я не смог распознать ваше сообщение", message_in)
            return FUNC_RESPONSE
        
        encoded_text = result.encode('utf-8')

        config = configparser.ConfigParser()

        user_session = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                       region_name='ru-central1')
        user_resource = user_session.resource(service_name='s3', endpoint_url="https://storage.yandexcloud.net")

        my_bucket = user_resource.Bucket("itiscl-spr23-21-public")

        tts_resp = requests.post(url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize",
                                 headers = {'Authorization': AUTH_HEADER_VOICE},
                                 data = {'text': encoded_text})
        if tts_resp.ok:
            body = tts_resp.text.decode('utf-8')
            my_bucket.put_object(Body=body,  Key='speech.raw')
            send_voice('speech.raw', message_in)
            return FUNC_RESPONSE


        send_voice('speech.ogg', message_in)
        return FUNC_RESPONSE
    
    if 'location' in message_in:
        location = message_in['location']

        weather_data = get_weather_from_location(location)

        if weather_data == None:
            result = f"Я не знаю какая погода в этом месте."
        else:
            result = f"{weather_data['weather'][0]['description']}.\nТемпература {weather_data['main']['temp']} ℃, ощущается как {weather_data['main']['feels_like']} ℃.\nАтмосферное давление {weather_data['main']['pressure']} мм рт. ст.\nВлажность {weather_data['main']['humidity']} %.\nВидимость {weather_data['visibility']} метров.\nВетер {weather_data['wind']['speed']} м/с, направление ветра {degToCompass(weather_data['wind']['deg'])}.\nВосход солнца {convertUnixToTime(weather_data['sys']['sunrise'])} МСК. Закат {convertUnixToTime(weather_data['sys']['sunset'])} МСК.\n"
        
        send_message(result, message_in)
        return FUNC_RESPONSE

    # Выделяем текст и преобразуем регистр.
    # echo_text = message_in['text'].upper()

    # # Отправляем преобразованный текст пользователю.
    # send_message(echo_text, message_in)

    # Завершим облачную функцию с кодом 200, чтобы сервер Telegram Bot
    # API повторно не отправлял на обработку это сообщение.
    return FUNC_RESPONSE

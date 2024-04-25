import re
import wget
import os
import time
from speechkit import RecognitionLongAudio, Session
from speechkit.auth import generate_jwt
import os
from boto.s3.connection import S3Connection


# Парсинг урла записи BBB. Возвращает ID записи и домен BBB
def url_parse(url):
    url_splitted = re.split("/", url)
    MEETING_ID = url_splitted[6]
    DOMAIN = url_splitted[2]
    return MEETING_ID, DOMAIN

# Урл записи аудио BBB


def get_audio_url(MEETING_ID, DOMAIN):

    return f"https://{DOMAIN}/presentation/{MEETING_ID}/video/webcams.webm"


class Decoder:
    def write_text(self, meeting_id, text):
        file = open(meeting_id, "w")
        file.write(text)
        file.close()
        return os.path.abspath(meeting_id)

    async def decode(self, url):

        # Подключение к SpeechKit

        bucket_name = os.environ.get('BUCKET_NAME')
        service_account_id = os.environ.get('SERVICE_ACCOUNT_ID')
        key_id = os.environ.get('YANDEX_KEY_ID')
        private_key = os.environ.get(
            'YANDEX_PRIVATE_KEY').replace('\\n', '\n').encode()
        if not (bucket_name and service_account_id and key_id and private_key):
            return "Проверьте переменные окружения"
        try:
            jwt = generate_jwt(service_account_id, key_id, private_key)
        except Exception:
            return "Проверьте авторизованный ключ"
        try:
            session = Session.from_jwt(jwt)
        except Exception:
            return "Не удалось подключиться по авторизованному ключу"
        try:
            access_key_id, secret = RecognitionLongAudio.get_aws_credentials(
                session, service_account_id)
            recognize_long_audio = RecognitionLongAudio(session, service_account_id, bucket_name, aws_access_key_id=access_key_id,
                                                        aws_secret=secret)
        except Exception:
            return "Не удалось подключиться к SpeechKit"

        # Подключение к Object Storage

        try:
            os.environ['S3_USE_SIGV4'] = 'True'
            conn = S3Connection(
                host='storage.yandexcloud.net'
            )
            conn.auth_region_name = 'ru-central1'
            bucket = conn.get_bucket(bucket_name)
        except Exception:
            return "Не удалось подключиться к Object Storage"

        # Директория для загрузки записи

        PATH = "/tmp"

        # Загрузка записи в видео-формате если оно еще не было распознано, конвертация в OggOpus, удаление видео

        meeting_id, domain = url_parse(url)

        # Если было распознано, возрват результата

        try:
            bucket_objects = bucket.list()
        except Exception:
            return "Не удалось запросить объекты бакета"
        bucket_objects = [obj.key for obj in bucket_objects]
        if meeting_id in bucket_objects:
            return self.write_text(meeting_id, bucket.get_key(meeting_id).get_contents_as_string().decode())
        AUDIO_URL = get_audio_url(meeting_id, domain)
        wget.download(AUDIO_URL, out=PATH, bar=None)
        VIDEO_PATH = f"{PATH}/webcams.webm"
        AUDIO_PATH = f"{PATH}/{meeting_id}.opus"
        try:
            os.system(
                f"ffmpeg -i {VIDEO_PATH} -c:a libopus -b:a 64k {AUDIO_PATH} -hide_banner -loglevel error")
            os.remove(VIDEO_PATH)
        except Exception:
            return "Ошибка при работе с файлом записи"

        # Отправка в Speech Kit

        try:
            recognize_long_audio.send_for_recognition(
                AUDIO_PATH, sampleRateHertz='48000', rawResults=False
            )
        except Exception:
            return "Не удалось отправить запись в SpeechKit"

        # Ожидание ответа от Speech Kit

        while True:
            time.sleep(5)
            try:
                if recognize_long_audio.get_recognition_results():
                    break
            except Exception:
                return "Не удалось получить ответ от SpeechKit"

        # Получение ответа от Speech Kit в виде текста

        text = recognize_long_audio.get_raw_text()

        # Разъединить слипвшиеся слова

        pattern_unsplit = r"(?<!\d)(?=[A-ZА-ЯЁ])(?!\.[A-ZА-ЯЁ])(?![A-ZА-ЯЁ]\.)"
        words = re.split(pattern_unsplit, text)
        text = ' '.join(words)

        # Загрузка результата в Object Storage при условии отсутствия распознования этой записи

        try:
            bucket.new_key(meeting_id).set_contents_from_string(text)
        except Exception:
            return "Не удалось загрузить текст записи в бакет"
        os.remove(AUDIO_PATH)
        return self.write_text(meeting_id, text)

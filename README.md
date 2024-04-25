# YC-BBB-Audio-To-Text
Телеграм бот для расшифровки записи из *BigBlueButton* в текстовый формат с помощью *Yandex Speech Kit* & *Yandex Object Storage*.
# Идея:
1. Боту поступает сообщение с ссылкой на запись из *BBB*;
2. Проверка валидности ссылки;
3. Если запись ранее расшифровалась, то в ответ отправляется расшифровка.
4. Загрузка записи;
5. Конвертация записи в *OggOpus* с помощью *ffmpeg*;
6. Отправка записи в *Yandex Speech Kit*;
7. Получение ответа;
8. Загрузка расшифровки в бакет;
9. Отправка расшифровки.

# Установка
1. Создать *Object Storage*
2. Создать сервисный аккаунт с нужными роялми
3. Создать авторизованный ключ для сервисного аккаута
4. Создасть статический ключ доступа для сервисного аккаута
```
git clone https://github.com/kass1337/YC-BBB-Audio-To-Text.git
cd YC-BBB-Audio-To-Text
```
5. Заполнить *credentials* данными статического ключа доступа
6. Заполнить *yandexenv.list* телеграм-токеном, названием бакета в Object Storage, ID сервисного аккаунта, данными авторизованного ключа
```
docker build --tag "yc-bbb-audio-to-text"  .
docker run -it --env-file yandexenv.list yc-bbb-audio-to-text
```
# Использование
Телеграм-бот ожидает валидную ссылку на запись вебинара из *BigBlueButton*. В ответ он пришлет текстовый файл с расшифровкой записи. К сожалению, *Yandex Speech Kit* работает довольно долго для длинных записей, поэтому ожидание может затянуться.
*Бот подходит только для личного использования. Не реализована поддержка асинхронной обработки запросов*

# Библиотека boto3 (AWS SDK для Python) для работы с Yandex Object Storage.
# Библиотека requests потребуется для скачивания фотографии.
import boto3
import requests
import urllib.parse

# Зададим URL точки доступа к API Yandex Object Storage
YOS_ENDPOINT = 'https://storage.yandexcloud.net'

# Подготовим файл для экспериментов.
# Зададим URL фотографии Гвидо ван Россум
PHOTO_URL = "https://farm1.staticflickr.com/76/199907296_a602917e6d_o.jpg"
# Сделаем GET запрос для получения фотографии Гвидо ван Россум.
# В теле HTTP ответа от сервера будут двоичные данные (фотография).
photo_http_response = requests.get(url=PHOTO_URL)
# Сохраним тело ответа в файл, что бы потом файл загрузить в бакет.
photo_file = open('Guido_van_Rossum.jpg', 'wb')
photo_file.write(photo_http_response.content)
photo_file.close()

# Создадим специальный объект для сессии.
# При создании сессии укажем профиль из конфигурационных файлов AWS SDK.
# Если профиля с таким именем не будет, то будет использован профиль default.
admin_session = boto3.session.Session(profile_name='admin')

# Создадим объект для управления ресурсами Yandex Object Storage от имени
# сервисного аккаунта spr23-00-sa-admin.
admin_resource = admin_session.resource(service_name='s3', endpoint_url=YOS_ENDPOINT)

# Получим список существующих бакетов.
for bucket in admin_resource.buckets.all():
    print(bucket)

# Создадим новый бакет с именем itiscl-spr23-00-public
admin_pub_bucket = admin_resource.Bucket('itiscl-spr23-21-public')
admin_pub_bucket.create()

# Сделаем бакет публичным.
# Воспользуемся предопределённым ACL public-read
# Доступны https://cloud.yandex.ru/docs/storage/concepts/acl#predefined-acls

# Далее попробуем поработать ит имени другого сервисного аккаунта
# spr23-00-sa-uploader.
uploader_session = boto3.session.Session(profile_name='uploader')
uploader_resource = uploader_session.resource(service_name='s3', endpoint_url=YOS_ENDPOINT)

# Создадим ресурс для бакета itiscl-spr23-00-public
uploader_pub_bucket = uploader_resource.Bucket('itiscl-spr23-21-public')

# Создадим ресурс для объекта с ключом guido_van_rossum_obj.jpg
uploader_object = uploader_pub_bucket.Object('guido_van_rossum_obj.jpg')

# В объект загрузим файл с именем Guido_van_Rossum.jpg
# из текущего каталога
uploader_object.upload_file(Filename='Guido_van_Rossum.jpg')

# Напечатаем ссылку на объект Guido_van_Rossum.jpg
# Обязательно нужно обработать ключ объекта, что бы преобразовать и экранировать
# символы, которые не предусмотрены стандартом для URL
url1_key = urllib.parse.quote(uploader_object.key)
url1_bucket = uploader_object.bucket_name
# Сформируем ссылку по шаблону https://storage.yandexcloud.net/<bucket>/<key>
print(f"https://storage.yandexcloud.net/{url1_bucket}/{url1_key}")

# Сформируем контент и загрузи его в объект с ключом 'это простой текст.txt'
content = b'Hello, World!'
uploader_second_object = uploader_pub_bucket.Object('это простой текст.txt')
uploader_second_object.put(Body=content)

# Напечатаем ссылку на объект 'это простой текст.txt'.
# Обязательно нужно обработать ключ объекта, что бы преобразовать и экранировать
# символы, которые не предусмотрены стандартом для URL
url2_key = urllib.parse.quote(uploader_second_object.key)
url2_bucket = uploader_second_object.bucket_name
# Сформируем ссылку по шаблону https://storage.yandexcloud.net/<bucket>/<key>
print(f"https://storage.yandexcloud.net/{url2_bucket}/{url2_key}")

# Попробуем создать объекты с одинаковым префиксом в ключе и можно посмотреть
# как это отображается через веб-консоль
# https://console.cloud.yandex.ru/link/storage
uploader_obj1 = uploader_pub_bucket.Object('dir1/file11.txt')
uploader_obj1.put(Body=content)
uploader_obj2 = uploader_pub_bucket.Object('dir1/file12.txt')
uploader_obj2.put(Body=content)
uploader_obj3 = uploader_pub_bucket.Object('dir1/file13.txt')
uploader_obj3.put(Body=content)
uploader_obj4 = uploader_pub_bucket.Object('dir2/file21.txt')
uploader_obj4.put(Body=content)
uploader_obj5 = uploader_pub_bucket.Object('dir2/file22.txt')
uploader_obj5.put(Body=content)
uploader_obj6 = uploader_pub_bucket.Object('dir3/file31.txt')
uploader_obj6.put(Body=content)

# Просмотрим список объектов в бакете itiscl-spr23-00-public
for obj in uploader_pub_bucket.objects.all():
    print(obj.key, obj.size)

# Настроим бакет как хостинг для сайта. Настраивать бакет будем от имени
# сервисного аккаунта spr23-00-sa-admin.
# Создадим ресурс для конфигурации хостинга.
bucket_website = admin_pub_bucket.Website()
# Зададим суффикс для индексного документа.
index_document = {'Suffix': 'index.html'}
# Зададим объект с HTML страницей для вывода, если будет ошибка 4XX.
error_document = {'Key': 'error.html'}
# Активируем конфигурацию.
bucket_website.put(WebsiteConfiguration={'ErrorDocument': error_document, 'IndexDocument': index_document})
# Простой HTML документ.
html_content = b"<!DOCTYPE><html><head><title>Test page</title></head><body><h1>Test page</h1></body></html>"
# Создадим ресурс для объекта с ключом index.html.
html_object = admin_pub_bucket.Object('index.html')
# Заполним объект HTML странице. Обязательно укажем, что объект имеет тип 'text/html'.
html_object.put(Body=html_content, ContentType='text/html')
# Сформируем ссылку на веб-сайт. Откроем в браузере.
print(f"https://{admin_pub_bucket.name}.website.yandexcloud.net")

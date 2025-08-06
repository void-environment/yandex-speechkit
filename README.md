# Yandex SpeechKit - Распознавание речи из аудио

## Установка

### Подготовка проекта

1. Клонируйте репозиторий или скачайте файлы проекта

2. Создайте виртуальное окружение (рекомендуется):
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

### Настройка переменных окружения

1. Скопируйте пример конфигурации:
```bash
cp .env.example .env
```

2. Отредактируйте файл `.env` и добавьте ваши данные:
```env
YANDEX_CLOUD_IAM_TOKEN=your_iam_token_here
YANDEX_FOLDER_ID=your_folder_id_here
```


### Установка Yandex Cloud CLI

**Linux/macOS:**
```bash
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
source ~/.bashrc
```

**Windows:**
Скачайте установщик с [официального сайта](https://cloud.yandex.ru/docs/cli/quickstart#install)

**Проверка установки:**
```bash
~/yandex-cloud/bin/yc --version
```

### Получение OAuth токена

1. **Перейдите по ссылке:** https://oauth.yandex.ru/authorize?response_type=token&client_id=1a6990aa636648e9b2ef855fa7bec2fb
2. **Авторизуйтесь** в вашем Yandex аккаунте
3. **Разрешите доступ** приложению Yandex Cloud CLI
4. **Скопируйте полученный OAuth токен** (длинная строка символов)

⚠️ **Важно:** Сохраните токен в безопасном месте - он понадобится для инициализации CLI.

### Инициализация CLI

```bash
~/yandex-cloud/bin/yc init
```

**Что произойдет:**
1. CLI запросит OAuth токен - вставьте скопированный токен
2. Выберите облако (обычно есть только одно)
3. Выберите папку (folder) или создайте новую
4. Выберите зону доступности (по умолчанию подойдет)

### Получение IAM токена и Folder ID

**Получить IAM токен:**
```bash
~/yandex-cloud/bin/yc iam create-token
```
⏰ **Важно:** IAM токен действует 12 часов, после чего нужно получить новый.

**Получить Folder ID:**
```bash
~/yandex-cloud/bin/yc resource-manager folder list
```

**Пример вывода:**
```
+----------------------+--------+--------+--------+
|          ID          |  NAME  | LABELS | STATUS |
+----------------------+--------+--------+--------+
| b1g**********jl8fldt | default|        | ACTIVE |
+----------------------+--------+--------+--------+
```

Скопируйте значение из колонки `ID` - это ваш Folder ID.

### Обновление .env файла

```env
# Замените на ваши реальные значения
YANDEX_CLOUD_IAM_TOKEN=
YANDEX_FOLDER_ID=

# Опционально для JWT аутентификации
SERVICE_ACCOUNT_ID=
YANDEX_KEY_ID=
YANDEX_PRIVATE_KEY=
```


### Использование

```bash
# Базовое использование
python speech_to_text.py input/audio.ogg

# С указанием языка
python speech_to_text.py input/audio.mp3 en-US
```
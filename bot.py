import logging
from datetime import datetime, timedelta
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== НАСТРОЙКИ ====================
# ВАШ ТОКЕН БОТА (уже вставлен)
BOT_TOKEN = "8541563773:AAH7tfuds2DJH8xkjzQRmR7MUjLnUd_g1ss"

# ВАШ ID в Telegram (уже вставлен)
ADMIN_ID = 380079648

# Часовой пояс Москвы (UTC+3)
MOSCOW_TZ_OFFSET = 3

# Время напоминаний (по Москве)
REMINDER_1_HOUR = 10  # 10:00
REMINDER_2_HOUR = 18  # 18:00

# Даты адвента
ADVENT_START = datetime(2025, 12, 17).date()
ADVENT_END = datetime(2025, 12, 31).date()
# ==================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    """Создаем базу данных и таблицы"""
    conn = sqlite3.connect('advent_bot.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            last_reminder_day INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица наград
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            day INTEGER PRIMARY KEY,
            reward_text TEXT NOT NULL,
            reward_name TEXT NOT NULL
        )
    ''')
    
    # Таблица связей пользователь-награда
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            day INTEGER,
            opened INTEGER DEFAULT 0,
            activated INTEGER DEFAULT 0,
            open_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (day) REFERENCES rewards(day)
        )
    ''')
    
    # ЗАПОЛНЯЕМ НАГРАДЫ (то, что вы написали)
    rewards = [
        (17, '🎁 Награда за 17 декабря: Сертификат на фильм. Можешь выбрать любой фильм, сериал или видео, мы с тобой посмотрим без единой жалобы с моей стороны. Не более 3 часов.', 'Сертификат на фильм'),
        (18, '🎁 Награда за 18 декабря: Сертификат на поездку. Поедем с тобой куда хочешь (кроме Вологды).', 'Сертификат на поездку'),
        (19, '🎁 Награда за 19 декабря: Освобождение от посуды. Активируй сертификат когда захочешь чтобы я вымыл всю посуду.', 'Освобождение от посуды'),
        (20, '🎁 Награда за 20 декабря: Сертификат на косметику. Активируй сертификат и я куплю тебе любую косметику, которую ты выберешь.', 'Сертификат на косметику'),
        (21, '🎁 Награда за 21 декабря: Сертификат на «Вето». Сертификат позволяет один раз отменить любые мои планы (в разумных пределах, конечно), если тебе просто захочется провести время вместе или наоборот побыть одной.', 'Сертификат на «Вето»'),
        (22, '🎁 Награда за 22 декабря: Сертификат на победу в споре. Можно предъявить в любой момент чтобы победить в споре.', 'Сертификат на победу в споре'),
        (23, '🎁 Награда за 23 декабря: Сертификат на музыку. Полтора часа буду слушать твою музыку и не показывать отвращение.', 'Сертификат на музыку'),
        (24, '🎁 Награда за 24 декабря: Освобождение от похода в магазин. Активируй сертификат когда захочешь чтобы я самостоятельно сходил в магазин или составил тебе компанию.', 'Освобождение от похода в магазин'),
        (25, '🎁 Награда за 25 декабря: Сертификат на украшение. Покупаю тебе любое украшение в комнату для вайбика. Светяшку, игрушку, арома свечку или растение/цветок в горшке.', 'Сертификат на украшение'),
        (26, '🎁 Награда за 26 декабря: Сертификат на урок. Я учу тебя чему-то, что умею сам. Или наоборот - ты учишь меня чему-то своему, а я внимательный ученик.', 'Сертификат на урок'),
        (27, '🎁 Награда за 27 декабря: Сертификат на прощение. Ты можешь предъявить его, чтобы я без обид и обсуждений простил какую-то мелкую оплошность.', 'Сертификат на прощение'),
        (28, '🎁 Награда за 28 декабря: Сертификат на хобби. Это не просто сертификат на просмотр дурацкого шоу, а сертификат на день, в течении которого я буду заниматься с тобой теми вещами, которые тебе нравятся.', 'Сертификат на хобби'),
        (29, '🎁 Награда за 29 декабря: Сертификат «Королевы дня». С утра до вечера обращаюсь к тебе только «Ваше Величество», а также исполняю все твои мелкие прихоти с особым пиететом.', 'Сертификат «Королевы дня»'),
        (30, '🎁 Награда за 30 декабря: Сертификат на одну вещь из твоего виш-листа. Ну или того что у тебя в голове.', 'Сертификат на вещь из виш-листа'),
        (31, '🎁 Награда за 31 декабря: Сертификат на «Свидание вслепую». Я организую свидание на которое мы сходим. Перед активации убедись что мы не бедные в данный отрезок времени!', 'Сертификат на «Свидание вслепую»')
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO rewards (day, reward_text, reward_name) VALUES (?, ?, ?)', rewards)
    
    conn.commit()
    conn.close()
    print("База данных создана и заполнена!")

def get_db_connection():
    """Подключаемся к базе данных"""
    conn = sqlite3.connect('advent_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_moscow_time():
    """Получаем текущее время по Москве"""
    return datetime.utcnow() + timedelta(hours=MOSCOW_TZ_OFFSET)

def get_current_advent_day():
    """ВЕРСИЯ ДЛЯ ТЕСТА: Всегда возвращает 17 декабря"""
    # Закомментируйте старую логику, добавив решетки (#)
    # now_moscow = get_moscow_time()
    # today = now_moscow.date()
    #
    # if today < ADVENT_START:
    #     return None
    # if today > ADVENT_END:
    #     return None
    #
    # return (today - ADVENT_START).days + 1

    # Новая логика для теста
    test_day = 17  # Меняйте это число на 18, 19 и т.д., чтобы тестировать разные дни
    print(f"🔧 ТЕСТ: Функция возвращает день {test_day}")
    return test_day

def is_reward_opened_today(user_id):
    """Проверяем, открывал ли пользователь награду сегодня"""
    current_day = get_current_advent_day()
    if not current_day:
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM user_rewards WHERE user_id = ? AND day = ? AND opened = 1', (user_id, current_day))
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

# ==================== КОМАНДЫ БОТА ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем команду /start"""
    user = update.effective_user
    
    # Регистрируем пользователя
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                   (user.id, user.username, user.first_name, user.last_name))
    conn.commit()
    conn.close()
    
    # Создаем кнопки
    keyboard = [
        [InlineKeyboardButton("🎁 Открыть сегодняшнюю награду", callback_data='open_today')],
        [InlineKeyboardButton("📋 Мои открытые награды", callback_data='my_rewards')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🎄\n"
        f"Добро пожаловать в Адвент-календарь!\n\n"
        f"Каждый день с 17 по 31 декабря ты можешь открывать новые награды.\n"
        f"Нажимай кнопку ниже, чтобы открыть сегодняшнюю награду!",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем нажатия на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'open_today':
        await open_today_reward(query)
    elif query.data == 'my_rewards':
        await show_my_rewards(query)
    elif query.data == 'back_to_main':
        await back_to_main_menu(query)
    elif query.data == 'activate_menu':
        await ask_reward_number(query)

async def open_today_reward(query):
    """Открываем сегодняшнюю награду"""
    user_id = query.from_user.id
    current_day = get_current_advent_day()
    now_moscow = get_moscow_time()
    
    # Проверяем период адвента
    if current_day is None:
        if now_moscow.date() < ADVENT_START:
            await query.edit_message_text("🎅 Адвент-календарь еще не начался! Жди 17 декабря 2025 года!")
            return
        else:
            await query.edit_message_text("🎅 Адвент-календарь завершился! Спасибо за участие!")
            return
    
    # Проверяем, открывал ли уже сегодня
    if is_reward_opened_today(user_id):
        next_day = now_moscow.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        time_left = next_day - now_moscow
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        await query.edit_message_text(
            f"⏰ Сегодня ты уже открывал(а) награду!\n"
            f"Следующую можно открыть через {hours}ч {minutes}м",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 Мои награды", callback_data='my_rewards')]])
        )
        return
    
    # Получаем награду за сегодня
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT reward_text, reward_name FROM rewards WHERE day = ?', (current_day,))
    reward = cursor.fetchone()
    
    if reward:
        # Сохраняем, что пользователь открыл награду
        cursor.execute('INSERT INTO user_rewards (user_id, day, opened, open_date) VALUES (?, ?, 1, ?)',
                      (user_id, current_day, now_moscow))
        conn.commit()
        
        # Отправляем награду
        keyboard = [
            [InlineKeyboardButton("📋 Мои награды", callback_data='my_rewards')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        
        await query.edit_message_text(
            text=f"🎉 Ура! Ты открыл(а) награду за {current_day} декабря!\n\n{reward['reward_text']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    conn.close()

async def show_my_rewards(query):
    """Показываем все открытые награды пользователя"""
    user_id = query.from_user.id
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Берем только открытые награды (как вы просили)
    cursor.execute('''
        SELECT r.day, r.reward_name, ur.activated
        FROM user_rewards ur
        JOIN rewards r ON ur.day = r.day
        WHERE ur.user_id = ? AND ur.opened = 1
        ORDER BY r.day
    ''', (user_id,))
    
    rewards = cursor.fetchall()
    conn.close()
    
    if not rewards:
        text = "📭 У тебя пока нет открытых наград.\nОткрывай награды каждый день с помощью кнопки «Открыть сегодняшнюю награду»!"
    else:
        text = "📋 Твои открытые награды:\n\n"
        for reward in rewards:
            if reward['activated']:
                text += f"✅ {reward['day']} декабря: {reward['reward_name']} (АКТИВИРОВАНА)\n"
            else:
                text += f"🎁 {reward['day']} декабря: {reward['reward_name']}\n"
        
        text += "\nЧтобы активировать награду, нажми кнопку ниже и введи номер дня (например: 17)"
    
    # Кнопки
    keyboard = []
    if rewards:
        keyboard.append([InlineKeyboardButton("🔢 Активировать награду", callback_data='activate_menu')])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ask_reward_number(query):
    """Просим ввести номер награды для активации"""
    await query.edit_message_text(
        text="Введи номер награды (день декабря), которую хочешь активировать:\n\nНапример, для награды за 17 декабря введи: 17",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='my_rewards')]])
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем текстовые сообщения"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Проверяем, ввел ли пользователь число (для активации)
    if text.isdigit():
        day = int(text)
        
        if 17 <= day <= 31:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Проверяем, есть ли у пользователя эта награда и не активирована ли она
            cursor.execute('''
                SELECT ur.id, ur.activated, r.reward_name, u.first_name
                FROM user_rewards ur
                JOIN rewards r ON ur.day = r.day
                JOIN users u ON ur.user_id = u.user_id
                WHERE ur.user_id = ? AND ur.day = ? AND ur.opened = 1
            ''', (user_id, day))
            
            result = cursor.fetchone()
            
            if not result:
                await update.message.reply_text("❌ У тебя нет этой награды или ты ее еще не открыл(а)!")
            elif result['activated']:
                await update.message.reply_text("❌ Эта награда уже активирована!")
            else:
                # Активируем награду
                cursor.execute('UPDATE user_rewards SET activated = 1 WHERE id = ?', (result['id'],))
                
                # Отправляем уведомление админу (вам)
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"🎉 {result['first_name']} активировал(а) награду: \"{result['reward_name']}\""
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление админу: {e}")
                
                conn.commit()
                
                # Сообщение пользователю
                keyboard = [[InlineKeyboardButton("📋 Вернуться к наградам", callback_data='my_rewards')]]
                await update.message.reply_text(
                    f"✅ Награда \"{result['reward_name']}\" успешно активирована! Я получил уведомление!",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
            conn.close()
            return
    
    # Если сообщение "Открыть"
    if text.lower() == 'открыть':
        current_day = get_current_advent_day()
        if current_day:
            # Проверяем, открывал ли уже
            if is_reward_opened_today(user_id):
                await update.message.reply_text("Сегодня ты уже открывал(а) награду! Возвращайся завтра!")
            else:
                # Создаем fake query для открытия
                class FakeQuery:
                    def __init__(self, user):
                        self.from_user = user
                        self.data = 'open_today'
                    async def answer(self): pass
                    async def edit_message_text(self, **kwargs):
                        await update.message.reply_text(**kwargs)
                
                fake_query = FakeQuery(update.effective_user)
                await open_today_reward(fake_query)
        else:
            await update.message.reply_text("Сейчас не время адвента!")
    else:
        await update.message.reply_text("Используй кнопки в меню для навигации! 🎄")

async def back_to_main_menu(query):
    """Возвращаемся в главное меню"""
    keyboard = [
        [InlineKeyboardButton("🎁 Открыть сегодняшнюю награду", callback_data='open_today')],
        [InlineKeyboardButton("📋 Мои открытые награды", callback_data='my_rewards')]
    ]
    
    await query.edit_message_text(
        text="Главное меню:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Отправляем напоминания"""
    now_moscow = get_moscow_time()
    current_day = get_current_advent_day()
    
    if not current_day:
        return
    
    current_hour = now_moscow.hour
    
    if current_hour in [REMINDER_1_HOUR, REMINDER_2_HOUR]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем всех пользователей
        cursor.execute('SELECT user_id, last_reminder_day FROM users')
        users = cursor.fetchall()
        
        for user in users:
            # Проверяем, не отправляли ли уже напоминание сегодня
            if user['last_reminder_day'] != current_day:
                # Проверяем, открыл ли пользователь сегодняшнюю награду
                if not is_reward_opened_today(user['user_id']):
                    try:
                        await context.bot.send_message(
                            chat_id=user['user_id'],
                            text=f"⏰ Напоминание! Не забудь открыть сегодняшнюю награду за {current_day} декабря! 🎁"
                        )
                        cursor.execute('UPDATE users SET last_reminder_day = ? WHERE user_id = ?',
                                     (current_day, user['user_id']))
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Ошибка отправки напоминания: {e}")
        
        conn.close()

def main():
    """Основная функция"""
    # Создаем базу данных
    init_db()
    
    # Создаем приложение бота
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Настраиваем напоминания (каждые 30 минут проверяем)
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(send_reminders, interval=1800, first=10)
    
    # Запускаем бота
    print("Бот запущен! Нажми Ctrl+C для остановки.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':

    main()


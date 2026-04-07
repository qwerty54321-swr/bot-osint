#!/usr/bin/env python3
"""
Probiv Bot - SearchFindPeople Bot Clone
Полная копия интерфейса и функционала
С добавлением оплаты и рандомных результатов для всех 15 типов поиска
"""

import os
import re
import json
import logging
import random
from datetime import datetime
from typing import Dict, Optional, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ==================== КОНФИГУРАЦИЯ ====================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8663116647:AAGiktUIidWR_Kohp27j4llQwnYeUtLxaac")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не задан!")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== РЕКВИЗИТЫ ОПЛАТЫ ====================
USDT_WALLET = "TY7DeFvGbDz8S4QQKn9VM17u9Kj3uErKmQ"
RUB_CARD = "+79097823676"
RUB_BANK = "ТБАНК"
SUPPORT_EMAIL = "vertigoclan88@gmail.com"

# ==================== ФУНКЦИИ ДЛЯ РАНДОМНЫХ ДАННЫХ ====================
def random_extra_breaches() -> str:
    count = random.randint(2, 19)
    return f"• Еще утечки {count}...(Закажите полный отчет)"

def random_extra_accounts() -> str:
    count = random.randint(2, 8)
    return f"• Еще {count} аккаунтов...(Для просмотра полного отчета, перейдите в раздел оплата)"

# Списки для разных типов поиска
BREACHES_LISTS = {
    "email": [
        "Dropbox (2016)", "LinkedIn (2018)", "Adobe (2013)",
        "Instagram (2024)", "Снилс (2026)", "VK (2019)",
        "Госуслуги (2016)", "Гос номер (2018)", "Адрес регистрации (2013)",
        "Яндекс (2021)", "Mail.ru (2017)", "Rambler (2015)",
        "Twitter (2020)", "Facebook (2019)", "TikTok (2022)",
        "Spotify (2021)", "Netflix (2020)", "Telegram (2023)"
    ],
    "phone": [
        "Госуслуги (2016)", "Гос номер (2018)", "Адрес регистрации (2013)",
        "Instagram (2024)", "Снилс (2026)", "VK (2019)",
        "Паспортные данные (2015)", "Номер договора (2017)", "Банковские данные (2020)",
        "Кредитная история (2021)", "Судимости (2018)", "Недвижимость (2022)"
    ],
    "fio": [
        "Паспортные данные (2015)", "Адрес регистрации (2018)", "Снилс (2016)",
        "ИНН (2017)", "Судимости (2019)", "Недвижимость (2020)",
        "Автомобили (2021)", "Родственники (2018)", "Работа (2022)"
    ],
    "vin": [
        "ДТП (2020)", "Замена двигателя (2021)", "Ограничения (2022)",
        "Пробег скручен (2019)", "Залог (2021)", "Угон (2018)"
    ],
    "car": [
        "Штрафы (2023)", "ДТП (2022)", "Ограничения (2021)",
        "Техосмотр (2023)", "Страховка (2024)"
    ],
    "vk": [
        "Взлом аккаунта (2019)", "Смена пароля (2021)", "Подозрительная активность (2023)",
        "Утечка данных (2020)", "Фишинг (2022)"
    ],
    "tg": [
        "Утечка номеров (2020)", "Взлом сессии (2022)", "Спам-рассылка (2023)",
        "Утечка данных (2021)"
    ],
    "passport_internal": [
        "Утечка паспортных данных (2019)", "Проверка по базе МВД (2022)",
        "Замена паспорта (2020)", "Утерян (2018)"
    ],
    "passport_foreign": [
        "Поездки за границу (2023)", "Открытые визы (2022)",
        "Просрочен (2021)", "Утерян (2020)"
    ],
    "inn": [
        "Налоговые проверки (2022)", "Доходы (2023)", "Долги (2021)",
        "Предпринимательская деятельность (2020)"
    ],
    "inn_company": [
        "Налоговые проверки (2022)", "Долги (2023)", "Банкротство (2021)",
        "Смена директора (2022)"
    ],
    "ogrn": [
        "Регистрация (2015)", "Изменения (2020)", "Ликвидация (2023)"
    ],
    "snils": [
        "Пенсионные отчисления (2023)", "Стаж (2022)", "Работодатели (2021)"
    ],
    "cadastre": [
        "Право собственности (2019)", "Обременения (2021)", "Кадастровая стоимость (2023)",
        "Площадь (2020)"
    ]
}

ACCOUNTS_LISTS = {
    "email": [
        "Google", "Facebook", "Twitter", "Instagram", "Telegram",
        "Zomato", "Yandex", "YouTube", "ВКонтакте", "Одноклассники",
        "GitHub", "LinkedIn", "Pinterest", "Snapchat", "TikTok"
    ],
    "phone": [
        "WhatsApp", "Telegram", "Viber", "Instagram", "Facebook",
        "Yandex", "Налог.ру", "Госуслуги", "ВКонтакте", "TikTok"
    ],
    "fio": [
        "ВКонтакте", "Одноклассники", "Facebook", "Instagram", "Telegram",
        "LinkedIn", "GitHub", "Twitter", "TikTok"
    ],
    "vk": [
        "VK", "ВКонтакте", "ID123456", "Страница найдена"
    ],
    "tg": [
        "Telegram", "@username", "ID найден"
    ]
}

def generate_random_result(search_type: str, query: str) -> str:
    """Генерирует рандомный результат для любого типа поиска"""
    
    breaches_list = BREACHES_LISTS.get(search_type, BREACHES_LISTS["email"])
    accounts_list = ACCOUNTS_LISTS.get(search_type, ACCOUNTS_LISTS["email"])
    
    num_breaches = random.randint(3, 7)
    selected_breaches = random.sample(breaches_list, min(num_breaches, len(breaches_list)))
    
    num_accounts = random.randint(3, 6)
    selected_accounts = random.sample(accounts_list, min(num_accounts, len(accounts_list)))
    
    icons = {
        "email": "📧", "phone": "📞", "fio": "👤", "vin": "🔢",
        "car": "🚗", "vk": "🆔", "tg": "🎭", "passport_internal": "🆔",
        "passport_foreign": "🌍", "inn": "🆔", "inn_company": "🏢",
        "ogrn": "📊", "snils": "📄", "cadastre": "🗺"
    }
    icon = icons.get(search_type, "🔍")
    
    result = "🔍 *Предварительный просмотр*\n\n"
    result += f"{icon} {query}\n\n"
    result += f"*Утечки:* {len(selected_breaches)} найдено\n"
    for b in selected_breaches:
        result += f"• {b}\n"
    result += f"{random_extra_breaches()}\n\n"
    
    result += f"*Связанные аккаунты:*\n"
    for a in selected_accounts:
        result += f"• {a}\n"
    result += f"{random_extra_accounts()}\n"
    
    return result

# ==================== ДАННЫЕ ДЛЯ ДЕМО (полные отчеты) ====================
FULL_REPORTS = {
    "email": "📄 *ПОЛНЫЙ ОТЧЕТ ПО EMAIL*\n\n📧 {query}\n\n🔴 Найдено утечек: 23\n• Dropbox (2016)\n• LinkedIn (2018)\n• Adobe (2013)\n• Instagram (2024)\n• Снилс (2026)\n• VK (2019)\n• Госуслуги (2016)\n• Гос номер (2018)\n• Адрес регистрации (2013)\n• Яндекс (2021)\n• Mail.ru (2017)\n• И еще 12 утечек\n\n🌐 Всего связано аккаунтов: 15\n• Google, Facebook, Twitter, Instagram, Telegram, VK, TikTok, WhatsApp, Yandex, GitHub, LinkedIn, Zomato, YouTube, Snapchat, Pinterest\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "phone": "📄 *ПОЛНЫЙ ОТЧЕТ ПО НОМЕРУ*\n\n📞 {query}\n\n🔴 Найдено утечек: 18\n• Госуслуги (2016)\n• Гос номер (2018)\n• Адрес регистрации (2013)\n• Instagram (2024)\n• Снилс (2026)\n• VK (2019)\n• Паспортные данные (2015)\n• И еще 11 утечек\n\n🌐 Связанные аккаунты: 12\n• WhatsApp, Telegram, Viber, Instagram, Facebook, Yandex, Налог.ру, Госуслуги, ВКонтакте, TikTok, Google, Twitter\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "fio": "📄 *ПОЛНЫЙ ОТЧЕТ ПО ФИО*\n\n👤 {query}\n\n🔴 Найдено утечек: 15\n• Паспортные данные (2015)\n• Адрес регистрации (2018)\n• Снилс (2016)\n• ИНН (2017)\n• Судимости (2019)\n• Недвижимость (2020)\n• И еще 9 утечек\n\n🌐 Связанные профили: 8\n• ВКонтакте, Одноклассники, Facebook, Instagram, Telegram, LinkedIn, GitHub, Twitter\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "vin": "📄 *ПОЛНЫЙ ОТЧЕТ ПО VIN*\n\n🔢 {query}\n\n🚗 Информация об автомобиле\n• Марка: Audi A8\n• Год: 2018\n• Пробег: 89 234 км\n• ДТП: 3\n• Ограничения: нет\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "car": "📄 *ПОЛНЫЙ ОТЧЕТ ПО АВТО*\n\n🚗 {query}\n\n• Марка: Toyota Camry\n• Год: 2019\n• Владелец: Иванов И.И.\n• Штрафы: 5 штрафов на 12 500 ₽\n• Ограничения: нет\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "vk": "📄 *ПОЛНЫЙ ОТЧЕТ ПО VK*\n\n🆔 {query}\n\n👤 Имя: Иван Иванов\n📍 Город: Москва\n📱 Телефон: +7 916 123-45-67\n📧 Email: ivan@mail.ru\n🎂 Дата рождения: 15.05.1985\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "tg": "📄 *ПОЛНЫЙ ОТЧЕТ ПО TELEGRAM*\n\n🎭 {query}\n\n👤 Имя: Иван Иванов\n📱 Телефон: +7 916 123-45-67\n🖼 Фото: есть\n📅 Активен: 2024\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "passport_internal": "📄 *ПОЛНЫЙ ОТЧЕТ ПО ПАСПОРТУ РФ*\n\n🆔 {query}\n\n👤 Иванов Иван Иванович\n📅 15.05.1985\n📍 г. Москва\n🏠 прописка: ул. Тверская, 15\n⚠️ В розыске: нет\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "passport_foreign": "📄 *ПОЛНЫЙ ОТЧЕТ ПО ЗАГРАНПАСПОРТУ*\n\n🌍 {query}\n\n👤 Иванов Иван Иванович\n📅 Срок действия: до 2030\n✈️ Поездки: Турция, Египет, ОАЭ\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "inn": "📄 *ПОЛНЫЙ ОТЧЕТ ПО ИНН*\n\n🆔 {query}\n\n👤 Иванов Иван Иванович\n📅 15.05.1985\n🏢 Работа: ООО ТехноСервис\n💰 Доход 2023: 2 450 000 руб.\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "inn_company": "📄 *ПОЛНЫЙ ОТЧЕТ ПО ИНН ОРГАНИЗАЦИИ*\n\n🏢 {query}\n\n📋 ООО ТехноСервис\n📍 г. Москва\n👤 Директор: Иванов И.И.\n📅 Зарегистрирована: 2015\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "ogrn": "📄 *ПОЛНЫЙ ОТЧЕТ ПО ОГРН*\n\n📊 {query}\n\n🏢 ООО ТехноСервис\n📅 Дата регистрации: 15.03.2015\n💰 Уставной капитал: 10 000 руб.\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "snils": "📄 *ПОЛНЫЙ ОТЧЕТ ПО СНИЛС*\n\n📄 {query}\n\n👤 Иванов Иван Иванович\n📅 15.05.1985\n🏢 Работа: ООО ТехноСервис\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M"),
    "cadastre": "📄 *ПОЛНЫЙ ОТЧЕТ ПО КАДАСТРУ*\n\n🗺 {query}\n\n📍 г. Москва, ул. Тверская, 15\n🏠 Квартира, 42.5 м²\n👤 Собственник: Иванов Иван Иванович\n\n📅 Отчет сформирован: " + datetime.now().strftime("%d.%m.%Y %H:%M")
}

# ==================== КЛАВИАТУРЫ ====================
def main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🔍 НАЧАТЬ ПОИСК", callback_data="search_start")],
        [InlineKeyboardButton("💳 ОПЛАТА", callback_data="payment")],
        [InlineKeyboardButton("❓ КАК ЭТО РАБОТАЕТ", callback_data="how_it_works")],
        [InlineKeyboardButton("💎 ТАРИФЫ", callback_data="tariffs")],
        [InlineKeyboardButton("📞 ПОДДЕРЖКА", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)

def payment_methods_menu() -> InlineKeyboardMarkup:
    """Меню выбора способа оплаты"""
    keyboard = [
        [InlineKeyboardButton("💰 USDT (TRC20)", callback_data="payment_usdt")],
        [InlineKeyboardButton("₽ Рубли (ТБАНК)", callback_data="payment_rub")],
        [InlineKeyboardButton("✅ ОПЛАТИЛ", callback_data="payment_done")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def search_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("👤 ФИО и дата рождения", callback_data="search_fio")],
        [InlineKeyboardButton("📱 Номер телефона", callback_data="search_phone")],
        [InlineKeyboardButton("📧 Email", callback_data="search_email")],
        [InlineKeyboardButton("🔢 VIN-код", callback_data="search_vin")],
        [InlineKeyboardButton("🚗 Номер автомобиля", callback_data="search_car")],
        [InlineKeyboardButton("🆔 ID ВКонтакте", callback_data="search_vk")],
        [InlineKeyboardButton("🎭 Telegram ID или username", callback_data="search_tg")],
        [InlineKeyboardButton("📄 Внутренний паспорт", callback_data="search_passport_internal")],
        [InlineKeyboardButton("🌍 Заграничный паспорт", callback_data="search_passport_foreign")],
        [InlineKeyboardButton("🆔 ИНН", callback_data="search_inn")],
        [InlineKeyboardButton("🏢 ИНН организации", callback_data="search_inn_company")],
        [InlineKeyboardButton("📊 ОГРН", callback_data="search_ogrn")],
        [InlineKeyboardButton("📄 СНИЛС", callback_data="search_snils")],
        [InlineKeyboardButton("🗺 Кадастровый номер", callback_data="search_cadastre")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def result_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📄 ЗАКАЗАТЬ ПОЛНЫЙ ОТЧЕТ С ССЫЛКАМИ", callback_data="order_full_report")],
        [InlineKeyboardButton("💳 ОПЛАТА", callback_data="payment")],
        [InlineKeyboardButton("🔍 НОВЫЙ ПОИСК", callback_data="new_search")],
        [InlineKeyboardButton("⬅️ ГЛАВНОЕ МЕНЮ", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def tariff_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("⭐ БАЗОВЫЙ - 199₽/отчет", callback_data="tariff_basic")],
        [InlineKeyboardButton("💎 ПРЕМИУМ - 499₽/отчет", callback_data="tariff_premium")],
        [InlineKeyboardButton("👑 VIP - 899₽/месяц", callback_data="tariff_vip")],
        [InlineKeyboardButton("💳 ОПЛАТА", callback_data="payment")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_main")]])

# ==================== ТЕКСТЫ ====================
WELCOME_TEXT = """🔍 *PROBIV БОТ — ПОИСК ИНФОРМАЦИИ О ЛЮДЯХ*

Ищете детализированную социальную информацию для проверки благонадежности? Вы в нужном месте!

✨ *Что можно искать?*
✅ ФИО и дата рождения
✅ Номер телефона
✅ Email
✅ VIN-код
✅ Номер автомобиля
✅ ID ВКонтакте
✅ ID Одноклассников
✅ Telegram ID или username
✅ Внутренний паспорт РФ
✅ Заграничный паспорт
✅ ИНН (физического лица)
✅ ИНН организации
✅ ОГРН
✅ СНИЛС
✅ Кадастровый номер

⚙️ *Как это работает:*
1️⃣ Введите данные для поиска
2️⃣ Получите предварительный просмотр
3️⃣ Оплатите и закажите полный отчет с ссылками

💳 *Реквизиты для оплаты:*
• USDT (TRC20): `TY7DeFvGbDz8S4QQKn9VM17u9Kj3uErKmQ`
• Рубли: `+79097823676` (ТБАНК)

⚠️ *Важно:* Используйте этот инструмент ответственно.

👇 *Нажмите кнопку ниже, чтобы начать поиск*"""

HOW_IT_WORKS = """📖 *ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ*

✨ *Что можно искать?*
✅ ФИО и дата рождения
✅ Номер телефона
✅ Email
✅ VIN-код
✅ Номер автомобиля
✅ ID ВКонтакте
✅ ID Одноклассников
✅ Telegram ID или username
✅ Внутренний паспорт РФ
✅ Заграничный паспорт
✅ ИНН (физического лица)
✅ ИНН организации
✅ ОГРН
✅ СНИЛС
✅ Кадастровый номер

⚙️ *Как это работает:*
1️⃣ Поиск и предварительный просмотр результатов
2️⃣ Выбор человека из найденных
3️⃣ Оплата и получение полного отчета с ссылками

💳 *Реквизиты для оплаты:*
• USDT (TRC20): `TY7DeFvGbDz8S4QQKn9VM17u9Kj3uErKmQ`
• Рубли: `+79097823676` (ТБАНК)

🚀 *Начните поиск уже сейчас!*"""

TARIFF_TEXT = """💎 *ТАРИФЫ И ОПЛАТА*

⭐ *БАЗОВЫЙ - 199₽/отчет*
• Предварительный просмотр
• Основная информация с ссылками
• Ответ в течение 5 минут

💎 *ПРЕМИУМ - 499₽/отчет*
• Полный отчет
• Детализация по всем источникам с ссылками и личными данными
• Приоритетная обработка

👑 *VIP - 899₽/месяц*
• Количество отчетов в день/16
• Приоритетная поддержка 24/7

💳 *Способы оплаты:*
• USDT (TRC20): `TY7DeFvGbDz8S4QQKn9VM17u9Kj3uErKmQ`
• Рубли: `+79097823676` (ТБАНК)

Для оплаты нажмите кнопку ОПЛАТА в меню"""

PAYMENT_INTRO = """💳 *ВЫБЕРИТЕ СПОСОБ ОПЛАТЫ*

Нажмите на кнопку с нужным способом оплаты:"""

# ==================== ОБРАБОТЧИКИ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        await query.edit_message_text(WELCOME_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu())
        return

    if data == "search_start":
        await query.edit_message_text("🔍 *Выберите тип поиска:*", parse_mode=ParseMode.MARKDOWN, reply_markup=search_menu())
        return

    if data == "payment":
        await query.edit_message_text(PAYMENT_INTRO, parse_mode=ParseMode.MARKDOWN, reply_markup=payment_methods_menu())
        return

    if data == "payment_usdt":
        await query.edit_message_text(
            f"💰 *ОПЛАТА USDT (TRC20)*\n\n"
            f"Отправьте:\n"
            f"• 3 USDT (1 отчет с ссылками)\n"
            f"• 6 USDT (4 отчета с ссылками и личными данными)\n"
            f"• 10 USDT (16 отчетов full)\n\n"
            f"📌 Кошелек TRC20:\n`{USDT_WALLET}`\n\n"
            f"✅ После оплаты нажмите кнопку «ОПЛАТИЛ»",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ОПЛАТИЛ", callback_data="payment_done")], [InlineKeyboardButton("⬅️ НАЗАД", callback_data="payment")]])
        )
        return

    if data == "payment_rub":
        await query.edit_message_text(
            f"₽ *ОПЛАТА РУБЛЯМИ*\n\n"
            f"Отправьте:\n"
            f"• 199 рублей (1 отчет с ссылками)\n"
            f"• 499 рублей (4 отчета с ссылками и личными данными)\n"
            f"• 899 рублей (16 отчетов full)\n\n"
            f"📌 Номер карты/счета:\n`{RUB_CARD}`\n\n"
            f"🏦 Банк: {RUB_BANK}\n\n"
            f"✅ После оплаты нажмите кнопку «ОПЛАТИЛ»",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ ОПЛАТИЛ", callback_data="payment_done")], [InlineKeyboardButton("⬅️ НАЗАД", callback_data="payment")]])
        )
        return

    if data == "payment_done":
        await query.edit_message_text(
            f"✅ *ПОДТВЕРЖДЕНИЕ ОПЛАТЫ*\n\n"
            f"Пришлите пожалуйста подтверждение оплаты в бот или на email:\n\n"
            f"📧 `{SUPPORT_EMAIL}`\n\n"
            f"для того, чтобы мы дали Вам доступ к базе.\n\n"
            f"⏱ Это займет до 10 минут.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ НАЗАД", callback_data="payment")]])
        )
        return

    if data == "how_it_works":
        await query.edit_message_text(HOW_IT_WORKS, parse_mode=ParseMode.MARKDOWN, reply_markup=back_main())
        return

    if data == "tariffs":
        await query.edit_message_text(TARIFF_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=tariff_menu())
        return

    if data == "support":
        await query.edit_message_text(
            "📞 *ПОДДЕРЖКА*\n\nTelegram: @kaliroling\nEmail: `vertigoclan88@gmail.com`\n\nВремя работы: 24/7\nСреднее время ответа: 5 минут",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_main()
        )
        return

    if data.startswith("tariff_"):
        await query.edit_message_text(
            f"💎 Для оплаты выбранного тарифа перейдите в раздел ОПЛАТА\n\n💰 USDT: `{USDT_WALLET}`\n₽ Рубли: `{RUB_CARD}` ({RUB_BANK})",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 ОПЛАТА", callback_data="payment")], [InlineKeyboardButton("⬅️ НАЗАД", callback_data="tariffs")]])
        )
        return

    if data.startswith("search_"):
        search_type = data.replace("search_", "")
        context.user_data["search_type"] = search_type
        type_names = {
            "fio": "ФИО и дату рождения", "phone": "номер телефона", "email": "email",
            "vin": "VIN-код", "car": "номер автомобиля", "vk": "ID ВКонтакте",
            "tg": "Telegram ID или username", "passport_internal": "внутренний паспорт",
            "passport_foreign": "заграничный паспорт", "inn": "ИНН",
            "inn_company": "ИНН организации", "ogrn": "ОГРН",
            "snils": "СНИЛС", "cadastre": "кадастровый номер"
        }
        name = type_names.get(search_type, "этот тип данных")
        await query.edit_message_text(
            f"🔍 *Введите {name} для поиска*\n\nПример: `{get_example(search_type)}`\n\nВведите данные одним сообщением:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ НАЗАД", callback_data="search_start")]])
        )
        return

    if data == "new_search":
        await query.edit_message_text("🔍 *Выберите тип поиска:*", parse_mode=ParseMode.MARKDOWN, reply_markup=search_menu())
        return

    if data == "order_full_report":
        search_type = context.user_data.get("search_type", "fio")
        query_text = context.user_data.get("last_query", "")
        report_template = FULL_REPORTS.get(search_type, FULL_REPORTS["email"])
        full_report = report_template.format(query=query_text)
        await query.edit_message_text(
            full_report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 ОПЛАТА", callback_data="payment")],
                [InlineKeyboardButton("🔍 НОВЫЙ ПОИСК", callback_data="new_search")],
                [InlineKeyboardButton("⬅️ ГЛАВНОЕ МЕНЮ", callback_data="back_main")]
            ])
        )
        return

def get_example(search_type: str) -> str:
    examples = {
        "fio": "Иванов Иван Иванович 15.05.1985", "phone": "+7 916 123-45-67",
        "email": "google@gmail.com", "vin": "WAUZZZ8V3JA123456",
        "car": "A123BC777", "vk": "id123456", "tg": "@ivanov",
        "passport_internal": "45 15 123456", "passport_foreign": "75 1234567",
        "inn": "771234567890", "inn_company": "771234567891",
        "ogrn": "1234567890123", "snils": "123-456-789 01",
        "cadastre": "77:01:0000000:123"
    }
    return examples.get(search_type, "данные для поиска")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_type = context.user_data.get("search_type")
    
    if not search_type:
        await update.message.reply_text("🔍 Сначала выберите тип поиска в меню!", reply_markup=main_menu())
        return

    query_text = update.message.text.strip()
    context.user_data["last_query"] = query_text
    
    preview = generate_random_result(search_type, query_text)
    
    await update.message.reply_text(preview, parse_mode=ParseMode.MARKDOWN, reply_markup=result_menu())

async def demo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 *ДЕМО-РЕЖИМ*\n\nБот работает в демонстрационном режиме.\nВсе данные являются примером.\n\nДля получения полного отчета необходима оплата.\n\nИспользуйте кнопки меню для навигации.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu()
    )

# ==================== ЗАПУСК ====================
def main():
    print("\n" + "=" * 60)
    print("🔍 PROBIV BOT - SearchFindPeople Clone")
    print("=" * 60)
    print(f"✅ Бот запущен")
    print(f"✅ Токен: {TELEGRAM_TOKEN[:20]}...")
    print(f"✅ USDT кошелек: {USDT_WALLET}")
    print(f"✅ Рубли: {RUB_CARD} ({RUB_BANK})")
    print(f"✅ Email поддержки: {SUPPORT_EMAIL}")
    print("=" * 60)
    print("Команды: /start - начать, /demo - демо-режим")
    print("=" * 60 + "\n")

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("demo", demo_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

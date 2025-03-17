from __future__ import annotations
import re
import time
from os.path import exists
from typing import TYPE_CHECKING

import telebot
from telebot.types import Message

if TYPE_CHECKING:
    from e import e

from logging import getLogger

import FunPayAPI.types
from FunPayAPI.account import Account
from tg_bot import static_keyboards as skb

NAME = "Delete all lots"
VERSION = "1.0"
DESCRIPTION = "Этот плагин позволяет быстро удалить все лоты на аккаунте.\n 📂 Плагины для FPC - https://t.me/menzo_files"
CREDITS = "@menzo2612"
UUID = "e2416edd-db53-40fd-b519-f8de42d91742"
SETTINGS_PAGE = False

RUNNING = False

logger = getLogger("FPC.lots_copy_plugin")

def escape_markdown(text: str) -> str:
    return re.sub(r'([_\*\[\]()~`>#+-=|{}.!])', r'\\\1', text)

def init_commands(e: e):
    if not e.telegram:
        return
    tg = e.telegram
    bot = e.telegram.bot

    def get_current_account(tg_msg: Message) -> FunPayAPI.types.UserProfile:
        attempts = 3
        while attempts:
            try:
                profile = e.account.get_user(e.account.id)
                return profile
            except:
                time.sleep(1)
                attempts -= 1
        else:
            bot.send_message(tg_msg.chat.id, "❌ Не удалось получить данные текущего профиля. Попробуйте позже. 😵")
            raise Exception

    def delete_lots(m: Message):
        global RUNNING
        if RUNNING:
            bot.send_message(m.chat.id, "❌ Процесс очистки лотов уже начался! 🚨\n"
                                        "Пожалуйста, дождитесь завершения текущего процесса или перезапустите бота. 🔄")
            return
        RUNNING = True
        try:
            profile = get_current_account(m)
            lots = profile.get_lots()
            deleted_lots_count = 0
            start_time = time.time()

            lot_ids_to_delete = [lot.id for lot in lots if lot.subcategory.type != FunPayAPI.types.SubCategoryTypes.CURRENCY]

            BATCH_SIZE = 1000
            for i in range(0, len(lot_ids_to_delete), BATCH_SIZE):
                batch = lot_ids_to_delete[i:i + BATCH_SIZE]
                try:
                    for lot_id in batch:
                        e.account.delete_lot(lot_id)
                        deleted_lots_count += 1
                        logger.info(f"🗑️ Удалил лот ID: {lot_id}")
                    time.sleep(1)
                except Exception as ex:
                    error_message = f"❌ Не удалось удалить пачку лотов. Попробуйте позже. 😵\nОшибка: {str(ex)}\nПропускаю. 🚫"
                    continue

            end_time = time.time()
            elapsed_time = end_time - start_time

            RUNNING = False
            success_message = f"✅ Очистка активных лотов завершена! 🎉\nУдалено лотов: {deleted_lots_count}\nЗатраченное время: {elapsed_time:.2f} секунд. ⏱️"
            bot.send_message(m.chat.id, success_message, parse_mode='Markdown')
        except Exception as ex:
            RUNNING = False
            error_message = f"❌ Произошла ошибка при удалении лотов. Попробуйте позже. 😵\nОшибка: {str(ex)}"
            bot.send_message(m.chat.id, escape_markdown(error_message), parse_mode='Markdown')
            return

    e.add_telegram_commands(UUID, [
        ("delete_lots", "удаляет все активные лоты на текущем аккаунте", True),
    ])

    tg.msg_handler(delete_lots, commands=["delete_lots"])

BIND_TO_PRE_INIT = [init_commands]
BIND_TO_DELETE = None

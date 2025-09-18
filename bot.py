import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ConversationHandler,
    MessageHandler, filters, ContextTypes, CallbackQueryHandler
)
import logica

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

(ASK_DATE, ASK_MILEAGE, ASK_SERVICE, ASK_COST, ASK_PLACE, ASK_LITERS) = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("📊 Recordatorios", callback_data="reminders")],
        [InlineKeyboardButton("🔧 Añadir Mantenimiento", callback_data="add_maintenance")],
        [InlineKeyboardButton("📖 Ver Historial", callback_data="history")],
        [InlineKeyboardButton("💰 Control Gastos", callback_data="expenses")],
        [InlineKeyboardButton("⛽ Añadir Gasolina", callback_data="add_fuel")],
        [InlineKeyboardButton("📈 Resumen Gasolina", callback_data="fuel_summary")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "👋 ¡Hola! Soy tu asistente de mantenimiento para la Honda CG 110.\n\nSelecciona una opción:"
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operación cancelada.")
    await start(update.message, context)
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    actions = {"reminders": logica.get_reminders, "history": logica.get_maintenance_history,
               "expenses": logica.get_expense_summary, "fuel_summary": logica.get_fuel_summary}
    if query.data in actions:
        message = actions[query.data]()
        await query.edit_message_text(text=message, parse_mode='Markdown')
        keyboard = [[InlineKeyboardButton("⬅️ Volver al Menú", callback_data="main_menu")]]
        await query.message.reply_text("Pulsa para volver:", reply_markup=InlineKeyboardMarkup(keyboard))

async def add_maintenance_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Ok, vamos a añadir un nuevo mantenimiento.\n\nFecha (YYYY-MM-DD)? (/cancelar para salir)")
    return ASK_DATE

async def ask_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['record'] = {'date': update.message.text}
    await update.message.reply_text("Kilometraje?")
    return ASK_MILEAGE

async def ask_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['record']['mileage'] = update.message.text
    await update.message.reply_text("Servicio realizado?")
    return ASK_SERVICE

async def ask_cost_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['record']['service'] = update.message.text
    await update.message.reply_text("Costo?")
    return ASK_COST

async def ask_place(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['record']['cost'] = update.message.text
    await update.message.reply_text("Lugar/Mecánico?")
    return ASK_PLACE

async def save_maintenance_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['record']['place'] = update.message.text
    try:
        logica.add_maintenance_record(context.user_data['record'])
        await update.message.reply_text("✅ ¡Registro de mantenimiento guardado!")
    except (ValueError, KeyError) as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        context.user_data.clear()
        await start(update.message, context)
        return ConversationHandler.END

async def add_fuel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Ok, vamos a añadir una recarga de gasolina.\n\nFecha (YYYY-MM-DD)? (/cancelar para salir)")
    return ASK_DATE

async def ask_liters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['record']['mileage'] = update.message.text
    await update.message.reply_text("Litros cargados?")
    return ASK_LITERS

async def ask_cost_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['record']['liters'] = update.message.text
    await update.message.reply_text("Costo total?")
    return ASK_COST

async def save_fuel_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['record']['cost'] = update.message.text
    try:
        logica.add_fuel_record(context.user_data['record'])
        await update.message.reply_text("✅ ¡Registro de gasolina guardado!")
    except (ValueError, KeyError) as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        context.user_data.clear()
        await start(update.message, context)
        return ConversationHandler.END

def main() -> None:
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_API_TOKEN no encontrado en .env")
        return
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    maint_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_maintenance_start, '^add_maintenance$')],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_mileage)],
            ASK_MILEAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_service)],
            ASK_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_cost_maintenance)],
            ASK_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_place)],
            ASK_PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_maintenance_record)],
        }, fallbacks=[CommandHandler("cancelar", cancel)])

    fuel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_fuel_start, '^add_fuel$')],
        states={
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_mileage)],
            ASK_MILEAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_liters)],
            ASK_LITERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_cost_fuel)],
            ASK_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_fuel_record)],
        }, fallbacks=[CommandHandler("cancelar", cancel)])

    application.add_handler(CommandHandler("start", start))
    application.add_handler(maint_conv)
    application.add_handler(fuel_conv)
    application.add_handler(CallbackQueryHandler(button_handler, '^(reminders|history|expenses|fuel_summary)$'))
    application.add_handler(CallbackQueryHandler(back_to_main_menu, '^main_menu$'))

    logger.info("Iniciando bot...")
    application.run_polling()

if __name__ == "__main__":
    main()

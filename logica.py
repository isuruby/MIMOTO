import json
import datetime

DATA_FILE = "moto_data.json"

# --- Funciones de Gestión de Datos ---

def load_data():
    """Carga los datos desde el archivo JSON."""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "motorcycle": "Honda CG 110",
            "current_mileage": 0,
            "last_updated_date": "",
            "maintenance_history": [],
            "fuel_history": [],
            "service_intervals": {
                "Cambio de aceite": 1000,
                "Filtro de aire": 3000,
                "Ajuste de cadena": 3000,
                "Cambio de bujía": 6000,
                "Revisión general": 12000
            }
        }

def save_data(data):
    """Guarda los datos en el archivo JSON."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Funciones de Lógica de Mantenimiento ---

def get_reminders():
    """Formatea los recordatorios de próximos servicios."""
    data = load_data()
    current_mileage = data["current_mileage"]
    history = data.get("maintenance_history", [])
    intervals = data.get("service_intervals", {})

    message = f"**📊 Recordatorios de Próximos Servicios**\n"
    message += f"Kilometraje actual: {current_mileage} km\n\n"

    for service, interval in intervals.items():
        last_service_mileage = 0
        for record in sorted(history, key=lambda x: x["mileage"], reverse=True):
            if service.lower() in record["service"].lower():
                last_service_mileage = record["mileage"]
                break

        next_service_mileage = last_service_mileage + interval
        km_remaining = next_service_mileage - current_mileage

        if km_remaining <= 0:
            message += f"🔴 **{service}**: ¡Servicio requerido! (Vencido por {-km_remaining} km)\n"
        else:
            message += f"🟢 **{service}**: Próximo en {km_remaining} km (a los {next_service_mileage} km)\n"

    return message

def get_maintenance_history():
    """Formatea el historial de mantenimiento."""
    data = load_data()
    history = data.get("maintenance_history", [])
    if not history:
        return "No hay registros de mantenimiento."

    message = "**📖 Historial de Mantenimiento**\n\n"
    for record in sorted(history, key=lambda x: x["date"], reverse=True):
        message += (
            f"📅 **Fecha**: {record['date']}\n"
            f"📈 **Kilometraje**: {record['mileage']} km\n"
            f"🔧 **Servicio**: {record['service']}\n"
            f"💰 **Costo**: ${record['cost']:.2f}\n"
            f"👨‍🔧 **Lugar**: {record['place']}\n"
            f"--------------------\n"
        )
    return message

def add_maintenance_record(record_data):
    """Añade un nuevo registro de mantenimiento."""
    data = load_data()
    new_record = {
        "date": record_data['date'], "mileage": int(record_data['mileage']),
        "service": record_data['service'], "cost": float(record_data['cost']),
        "place": record_data['place'],
    }
    data["maintenance_history"].append(new_record)
    if new_record["mileage"] > data["current_mileage"]:
        data["current_mileage"] = new_record["mileage"]
        data["last_updated_date"] = new_record["date"]
    save_data(data)

def get_expense_summary():
    """Formatea el resumen de gastos."""
    data = load_data()
    history = data.get("maintenance_history", [])
    if not history:
        return "No hay registros de gastos."

    expenses_by_year, expenses_by_month = {}, {}
    for record in history:
        try:
            date = datetime.datetime.strptime(record["date"], "%Y-%m-%d")
            cost = float(record.get("cost", 0))
            expenses_by_year[date.year] = expenses_by_year.get(date.year, 0) + cost
            expenses_by_month[date.strftime("%Y-%m")] = expenses_by_month.get(date.strftime("%Y-%m"), 0) + cost
        except (ValueError, TypeError):
            continue

    message = "**💰 Control de Gastos**\n\n**Gastos por Año:**\n"
    message += "\n".join([f"- {year}: ${total:.2f}" for year, total in sorted(expenses_by_year.items())]) or "Sin datos."
    message += "\n\n**Gastos por Mes:**\n"
    message += "\n".join([f"- {month}: ${total:.2f}" for month, total in sorted(expenses_by_month.items())]) or "Sin datos."
    return message

# --- Funciones de Lógica de Gasolina ---

def add_fuel_record(record_data):
    """Añade un nuevo registro de gasolina."""
    data = load_data()
    new_record = {
        "date": record_data['date'], "mileage": int(record_data['mileage']),
        "liters": float(record_data['liters']), "cost": float(record_data['cost']),
    }
    data.setdefault("fuel_history", []).append(new_record)
    if new_record["mileage"] > data["current_mileage"]:
        data["current_mileage"] = new_record["mileage"]
        data["last_updated_date"] = new_record["date"]
    save_data(data)

def get_fuel_summary():
    """Formatea el rendimiento promedio de gasolina."""
    data = load_data()
    fuel_history = sorted(data.get("fuel_history", []), key=lambda x: x["mileage"])
    if len(fuel_history) < 2:
        return "⛽ Se necesitan al menos dos registros de gasolina para calcular el rendimiento."

    total_km, total_liters = 0, 0
    for i in range(len(fuel_history) - 1):
        km_diff = fuel_history[i+1]["mileage"] - fuel_history[i]["mileage"]
        liters_consumed = fuel_history[i]["liters"]
        if km_diff > 0 and liters_consumed > 0:
            total_km += km_diff
            total_liters += liters_consumed

    if total_liters == 0:
        return "No hay suficientes datos para calcular un rendimiento válido."

    avg_perf = total_km / total_liters
    return (f"**📈 Resumen de Gasolina**\n\n"
            f"Kilómetros analizados: {total_km} km\n"
            f"Litros consumidos: {total_liters:.2f} L\n\n"
            f"**Rendimiento promedio: {avg_perf:.2f} km/L**")

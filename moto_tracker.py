import json
import datetime

DATA_FILE = "moto_data.json"

def load_data():
    """Loads data from the JSON file."""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def save_data(data):
    """Saves data to the JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def display_history(data):
    """Displays the complete maintenance history."""
    print("\n--- Historial de Mantenimiento ---")
    history = data.get("maintenance_history", [])
    if not history:
        print("No hay registros de mantenimiento.")
        return

    for record in sorted(history, key=lambda x: x["date"]):
        print(
            f"Fecha: {record['date']}, Kilometraje: {record['mileage']} km, "
            f"Servicio: {record['service']}, Costo: ${record['cost']:.2f}, "
            f"Lugar/Mecánico: {record['place']}"
        )

def add_maintenance_record(data):
    """Adds a new maintenance record."""
    print("\n--- Agregar Nuevo Registro de Mantenimiento ---")
    try:
        date_str = input("Fecha (YYYY-MM-DD): ")
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        mileage = int(input("Kilometraje: "))
        service = input("Servicio realizado: ")
        cost = float(input("Costo: "))
        place = input("Lugar/Mecánico: ")

        new_record = {
            "date": date,
            "mileage": mileage,
            "service": service,
            "cost": cost,
            "place": place,
        }

        data["maintenance_history"].append(new_record)
        if mileage > data["current_mileage"]:
            data["current_mileage"] = mileage
            data["last_updated_date"] = date

        save_data(data)
        print("Registro de mantenimiento agregado exitosamente.")
    except ValueError:
        print("Entrada inválida. Por favor, asegúrese de que el kilometraje y el costo sean números.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

def calculate_next_services(data):
    """Calculates the next service dates/mileage."""
    reminders = {}
    current_mileage = data["current_mileage"]
    history = data.get("maintenance_history", [])
    intervals = data.get("service_intervals", {})

    for service, interval in intervals.items():
        last_service_mileage = 0
        for record in sorted(history, key=lambda x: x["mileage"], reverse=True):
            if service.lower() in record["service"].lower():
                last_service_mileage = record["mileage"]
                break

        next_service_mileage = last_service_mileage + interval
        km_until_next_service = next_service_mileage - current_mileage
        reminders[service] = {
            "next_service_km": next_service_mileage,
            "km_remaining": km_until_next_service
        }
    return reminders

def display_reminders(data):
    """Displays reminders for upcoming services."""
    print("\n--- Recordatorios de Próximos Servicios ---")
    print(f"Kilometraje actual: {data['current_mileage']} km")
    reminders = calculate_next_services(data)
    for service, details in reminders.items():
        if details['km_remaining'] <= 0:
            print(f"- {service}: ¡Servicio requerido! (Vencido por {-details['km_remaining']} km)")
        else:
            print(f"- {service}: Próximo en {details['km_remaining']} km (a los {details['next_service_km']} km)")

def display_expense_summary(data):
    """Displays a summary of expenses."""
    print("\n--- Control de Gastos ---")
    history = data.get("maintenance_history", [])
    if not history:
        print("No hay registros de gastos.")
        return

    expenses_by_year = {}
    expenses_by_month = {}

    for record in history:
        date = datetime.datetime.strptime(record["date"], "%Y-%m-%d")
        year = date.year
        month = date.strftime("%Y-%m")
        cost = record["cost"]

        expenses_by_year[year] = expenses_by_year.get(year, 0) + cost
        expenses_by_month[month] = expenses_by_month.get(month, 0) + cost

    print("\nGastos por Año:")
    for year, total in sorted(expenses_by_year.items()):
        print(f"- {year}: ${total:.2f}")

    print("\nGastos por Mes:")
    for month, total in sorted(expenses_by_month.items()):
        print(f"- {month}: ${total:.2f}")

def main():
    """Main function to run the application."""
    data = load_data()
    if not data:
        print("No se encontró el archivo de datos. Por favor, asegúrese de que 'moto_data.json' existe.")
        return

    while True:
        print("\n--- Sistema de Seguimiento de Mantenimiento de Motocicleta ---")
        print(f"Motocicleta: {data['motorcycle']}")
        print(f"Kilometraje Actual: {data['current_mileage']} km (Actualizado al {data['last_updated_date']})")
        print("\nOpciones:")
        print("1. Ver Recordatorios de Próximos Servicios")
        print("2. Agregar Registro de Mantenimiento")
        print("3. Ver Historial de Mantenimiento")
        print("4. Ver Control de Gastos")
        print("5. Salir")

        choice = input("Seleccione una opción: ")

        if choice == '1':
            display_reminders(data)
        elif choice == '2':
            add_maintenance_record(data)
            data = load_data() # Recargar datos después de agregar un registro
        elif choice == '3':
            display_history(data)
        elif choice == '4':
            display_expense_summary(data)
        elif choice == '5':
            print("¡Hasta luego!")
            break
        else:
            print("Opción no válida. Por favor, intente de nuevo.")

if __name__ == "__main__":
    main()

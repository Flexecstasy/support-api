import requests
import os

BASE_URL = "http://localhost:8000"
UPLOADS_DIR = r".\uploads"  # локальная папка с тестовыми файлами

# ----------------------------
# Создать тикет с фото
# ----------------------------
ticket_file_path = os.path.join(UPLOADS_DIR, "Warframe0000.jpg")
with open(ticket_file_path, "rb") as f:
    files = {"photo": (os.path.basename(ticket_file_path), f, "image/jpeg")}
    data = {
        "full_name": "Иван Иванов",
        "contact": "ivan@example.com",
        "description": "Кнопка не работает"
    }
    response = requests.post(f"{BASE_URL}/tickets/", data=data, files=files)
ticket1 = response.json()
print("Создан тикет с фото:")
print(ticket1)
print("\n" + "-"*50 + "\n")

# ----------------------------
# Создать тикет без фото
# ----------------------------
data = {
    "full_name": "Мария Петрова",
    "contact": "maria@example.com",
    "description": "Ошибка при оплате"
}
response = requests.post(f"{BASE_URL}/tickets/", data=data)
ticket2 = response.json()
print("Создан тикет без фото:")
print(ticket2)
print("\n" + "-"*50 + "\n")

# ----------------------------
#  Добавить ответ специалиста к первому тикету
# ----------------------------
response_file_path = os.path.join(UPLOADS_DIR, "Warframe0001.jpg")
with open(response_file_path, "rb") as f:
    files = {"media": (os.path.basename(response_file_path), f, "image/jpeg")}
    data = {
        "responder_name": "Support Team",
        "status": "resolved",
        "text": "Проблема исправлена, перезапустите приложение"
    }
    response = requests.post(f"{BASE_URL}/tickets/{ticket1['id']}/response", data=data, files=files)
response1 = response.json()
print(f"Добавлен ответ к тикету {ticket1['id']}:")
print(response1)
print("\n" + "-"*50 + "\n")

# ----------------------------
#  Получить тикет по ID
# ----------------------------
response = requests.get(f"{BASE_URL}/tickets/{ticket1['id']}")
ticket_with_response = response.json()
print(f"Тикет с ID {ticket1['id']} с ответом:")
print(ticket_with_response)
print("\n" + "-"*50 + "\n")

# ----------------------------
#  Получить список всех тикетов
# ----------------------------
response = requests.get(f"{BASE_URL}/tickets/?skip=0&limit=10")
tickets_list = response.json()
print("Список всех тикетов:")
for t in tickets_list:
    print(t)
    print("-"*30)

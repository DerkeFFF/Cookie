import pyautogui
import time
from datetime import datetime
import os

# 1. Создаём папку для скриншотов, если её нет
save_dir = "screenshots"
os.makedirs(save_dir, exist_ok=True)

print("Начинаю делать скриншоты каждые 5 секунд...")
print("Переключись на окно с игрой! Нажми Ctrl+C в этом терминале, чтобы остановить.\n")

count = 0

try:
    while True:
        # Делаем снимок экрана
        screenshot = pyautogui.screenshot()
        
        # Генерируем уникальное имя файла с датой и временем
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{save_dir}/screenshot_{timestamp}.png"
        
        # Сохраняем картинку
        screenshot.save(filename)
        count += 1
        
        print(f"[{count}] Сохранено: {filename}")
        
        # Ждём 5 секунд перед следующим снимком
        time.sleep(5)
        
except KeyboardInterrupt:
    print(f"\nСбор остановлен. Всего сделано скриншотов: {count}")

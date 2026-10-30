import sys
import ctypes
import time
import pyautogui
import cv2
import numpy as np
from ultralytics import YOLO
import keyboard

# =====================================================================
#                          БЛОК НАСТРОЕК (КОНФИГ)
# =====================================================================
CONFIG = {
    # Путь к вашей сконвертированной ONNX-модели
    "model_path": "runs/detect/cookie_detector-6/weights/best.onnx", 
    
    # Настройки уверенности
    "conf_default": 0.35,     
    "conf_close_ad": 0.50,    
    "conf_game_cookie": 0.40, 
    
    # Тайминги
    "cooldown_purchase": 5.0,  # Пауза в секундах МЕЖДУ закупками (после того как бот скупит всё доступное)
    "delay_after_click": 0.2,  # Пауза между кликами по разным апгрейдам, чтобы игра успевала засчитать покупку
    "cookie_clicks_count": 30, # Количество кликов по печеньке за раз
    "cookie_click_delay": 0.01,
    
    "hotkey_pause": "space"    
}

# =====================================================================
if sys.platform == 'win32':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

is_paused = False
last_purchase_time = 0.0  

print(f"Загрузка ONNX-модели YOLO: {CONFIG['model_path']}...")
# Ultralytics автоматически задействует onnxruntime для .onnx файлов
model = YOLO(CONFIG["model_path"], task="detect")

# Вытаскиваем имена классов из ONNX метаданных
CLASS_NAMES = model.names
print(f"📋 Структура классов модели успешно инициализирована: {list(CLASS_NAMES.values())}")
print("=======================================================\n")

def toggle_pause():
    global is_paused
    is_paused = not is_paused
    if is_paused:
        print("\n⏸️ БОТ НА ПАУЗЕ. Нажмите ПРОБЕЛ...")
    else:
        print("\n▶️ БОТ ВОЗОБНОВИЛ РАБОТУ.")
    time.sleep(0.3)

keyboard.add_hotkey(CONFIG["hotkey_pause"], toggle_pause)

def process_game():
    global last_purchase_time
    
    screen_w, screen_h = pyautogui.size()
    
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    img_h, img_w, _ = screenshot_np.shape

    # Инференс ONNX-модели через среду Ultralytics (работает быстрее и ест меньше памяти)
    results = model(screenshot_np, verbose=False)
    
    detected_objects = {name: [] for name in CLASS_NAMES.values()}
    current_time = time.time()
    
    print("\n--- Сканирование экрана (ONNX) ---")

    for result in results:
        if result.boxes is None:
            continue
            
        for box in result.boxes:
            confidence = box.conf.item() if hasattr(box.conf, 'item') else float(box.conf[0])
            class_id = int(box.cls.item() if hasattr(box.cls, 'item') else int(box.cls[0]))
            
            if class_id in CLASS_NAMES:
                c_name = CLASS_NAMES[class_id]
                
                required_conf = CONFIG["conf_default"]
                if c_name == 'close_ad':
                    required_conf = CONFIG["conf_close_ad"]
                elif c_name == 'game':
                    required_conf = CONFIG["conf_game_cookie"]
                
                if confidence >= required_conf:
                    # При работе с ONNX координаты возвращаются в виде массивов NumPy
                    coords = box.xyxy.tolist()[0]
                    x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
                    
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    
                    click_x = int(cx * (screen_w / img_w))
                    click_y = int(cy * (screen_h / img_h))
                    
                    detected_objects[c_name].append((click_x, click_y))

    bought_something = False

    # 1. Реклама
    if 'close_ad' in detected_objects and detected_objects['close_ad']:
        cx, cy = detected_objects['close_ad'][0]
        print(f"🚨 Реклама! Кликаю закрыть: ({cx}, {cy})")
        pyautogui.click(cx, cy)
        time.sleep(1.0)
        return True 

    # 2. Покупка улучшений
    time_since_last_purchase = current_time - last_purchase_time
    
    if time_since_last_purchase < CONFIG["cooldown_purchase"]:
        remaining = CONFIG["cooldown_purchase"] - time_since_last_purchase
        print(f"⏳ Магазин на кулдауне. Осталось: {remaining:.1f} сек. Кликаем только печеньку!")
    else:
        purchase_queue = [name for name in CLASS_NAMES.values() if 'tool' in name or 'upgrade' in name]
        purchase_queue.sort() 
        
        for current_class in purchase_queue:
            if current_class in detected_objects and detected_objects[current_class]:
                for (cx, cy) in detected_objects[current_class]:
                    print(f"🛒 Покупаю улучшение: {current_class} ({cx}, {cy})")
                    pyautogui.click(cx, cy)
                    time.sleep(CONFIG["delay_after_click"])
                    bought_something = True
        
        if bought_something:
            last_purchase_time = time.time()  

    # 3. Клик по главной печеньке
    if 'game' in detected_objects and detected_objects['game']:
        cx, cy = detected_objects['game'][0]
        if bought_something:
            time.sleep(0.3) 
            
        print(f"🍪 Кликаю по печеньке {CONFIG['cookie_clicks_count']} раз(а): ({cx}, {cy})")
        for _ in range(CONFIG["cookie_clicks_count"]):
            if is_paused: 
                break
            pyautogui.click(cx, cy)
            time.sleep(CONFIG["cookie_click_delay"])
        return True

    return bought_something

# =====================================================================
print("Запуск ИИ-автокликера на базе ONNX.")
print(f"Управление: Нажмите [{CONFIG['hotkey_pause'].upper()}], чтобы поставить бота на ПАУЗУ.")
print("=======================================================\n")

while True:
    if is_paused:
        time.sleep(0.1)
        continue
        
    bot_action = process_game()
    
    if not bot_action:
        print("Ничего уверенно не найдено. Ожидание 1 сек...")
        time.sleep(1.0)

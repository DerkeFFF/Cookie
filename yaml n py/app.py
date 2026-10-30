"""ИИ-автокликер для Cookie Clicker на базе YOLO.

Порядок действий на каждом проходе:
    1. Закрыть рекламу (если найдена).
    2. Купить все доступные улучшения и постройки (с кулдауном).
    3. Накликать печеньку.

Пауза / продолжение — по горячей клавише (по умолчанию пробел).
"""

import ctypes
import sys
import time
from pathlib import Path

import cv2
import keyboard
import numpy as np
import pyautogui
from ultralytics import YOLO


# =====================================================================
#                              НАСТРОЙКИ
# =====================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "runs" / "detect" / "cookie_detector-6" / "weights" / "best.pt"

# Минимальная уверенность модели
CONF_DEFAULT = 0.35
CONF_CLOSE_AD = 0.50
CONF_GAME_COOKIE = 0.40

# Тайминги (в секундах)
COOLDOWN_PURCHASE = 5.0      # пауза между закупками
DELAY_AFTER_CLICK = 0.2      # пауза между покупками разных улучшений
COOKIE_CLICK_DELAY = 0.01    # пауза между кликами по печеньке
AD_CLOSE_DELAY = 1.0         # пауза после закрытия рекламы
IDLE_DELAY = 1.0             # пауза, если ничего не найдено
PAUSED_POLL_DELAY = 0.1      # как часто проверять снятие паузы

COOKIE_CLICKS_COUNT = 30     # кликов по печеньке за один проход

HOTKEY_PAUSE = "space"

# Имена классов
CLASS_GAME = "game"
CLASS_CLOSE_AD = "close_ad"
PURCHASE_MARKERS = ("tool", "upgrade")


# =====================================================================
#                           СОСТОЯНИЕ БОТА
# =====================================================================
is_paused = False
last_purchase_time = 0.0


# =====================================================================
#                              ИНИЦИАЛИЗАЦИЯ
# =====================================================================
def enable_dpi_awareness():
    """Чтобы координаты кликов совпадали с экраном при масштабировании Windows."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def toggle_pause():
    global is_paused
    is_paused = not is_paused
    if is_paused:
        print("\n⏸️ БОТ НА ПАУЗЕ. Нажмите ПРОБЕЛ...")
    else:
        print("\n▶️ БОТ ВОЗОБНОВИЛ РАБОТУ.")
    time.sleep(0.3)


enable_dpi_awareness()

print(f"Загрузка нейросети YOLO: {MODEL_PATH}...")
model = YOLO(str(MODEL_PATH))

# Настоящие имена классов берём из файла .pt
CLASS_NAMES = model.names
print("\n📋 Структура классов модели успешно инициализирована.")
print("=======================================================\n")

keyboard.add_hotkey(HOTKEY_PAUSE, toggle_pause)


# =====================================================================
#                             РАСПОЗНАВАНИЕ
# =====================================================================
def required_confidence(class_name):
    """Порог уверенности для конкретного класса."""
    if class_name == CLASS_CLOSE_AD:
        return CONF_CLOSE_AD
    if class_name == CLASS_GAME:
        return CONF_GAME_COOKIE
    return CONF_DEFAULT


def take_screenshot():
    """Скриншот экрана в формате BGR для OpenCV / YOLO."""
    screenshot = np.array(pyautogui.screenshot())
    return cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)


def detect_objects(frame):
    """Возвращает {имя_класса: [(x, y), ...]} с экранными координатами центров."""
    screen_w, screen_h = pyautogui.size()
    img_h, img_w, _ = frame.shape

    results = model(frame, verbose=False)
    detected = {name: [] for name in CLASS_NAMES.values()}

    print("\n--- Сканирование экрана ---")

    for result in results:
        for box in result.boxes:
            confidence = box.conf.item()
            class_id = int(box.cls.item())

            if class_id not in CLASS_NAMES:
                continue

            class_name = CLASS_NAMES[class_id]
            if confidence < required_confidence(class_name):
                continue

            x1, y1, x2, y2 = box.xyxy.tolist()[0]
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            # Пересчёт из координат кадра в координаты экрана
            click_x = int(center_x * (screen_w / img_w))
            click_y = int(center_y * (screen_h / img_h))

            detected[class_name].append((click_x, click_y))

    return detected


# =====================================================================
#                                ДЕЙСТВИЯ
# =====================================================================
def close_ad(position):
    x, y = position
    print(f"🚨 Реклама! Кликаю закрыть: ({x}, {y})")
    pyautogui.click(x, y)
    time.sleep(AD_CLOSE_DELAY)


def buy_upgrades(detected):
    """Кликает по всем найденным улучшениям. Возвращает True, если что-то куплено."""
    purchase_queue = sorted(
        name for name in CLASS_NAMES.values()
        if any(marker in name for marker in PURCHASE_MARKERS)
    )

    bought_something = False
    for class_name in purchase_queue:
        for x, y in detected.get(class_name, []):
            print(f"🛒 Покупаю улучшение: {class_name} ({x}, {y})")
            pyautogui.click(x, y)
            time.sleep(DELAY_AFTER_CLICK)
            bought_something = True

    return bought_something


def click_cookie(position, after_purchase):
    x, y = position
    if after_purchase:
        time.sleep(0.3)  # даём интерфейсу обновиться после закупки

    print(f"🍪 Кликаю по печеньке {COOKIE_CLICKS_COUNT} раз(а): ({x}, {y})")
    for _ in range(COOKIE_CLICKS_COUNT):
        if is_paused:
            break
        pyautogui.click(x, y)
        time.sleep(COOKIE_CLICK_DELAY)


# =====================================================================
#                              ОДИН ПРОХОД
# =====================================================================
def process_game():
    """Один цикл: скан экрана и действия. True — если что-то было сделано."""
    global last_purchase_time

    frame = take_screenshot()
    detected = detect_objects(frame)
    current_time = time.time()

    # 1. Реклама — всегда в приоритете
    if detected.get(CLASS_CLOSE_AD):
        close_ad(detected[CLASS_CLOSE_AD][0])
        return True

    # 2. Покупка улучшений
    bought_something = False
    since_last_purchase = current_time - last_purchase_time

    if since_last_purchase < COOLDOWN_PURCHASE:
        remaining = COOLDOWN_PURCHASE - since_last_purchase
        print(f"⏳ Магазин на кулдауне. Осталось: {remaining:.1f} сек. Кликам только печеньку!")
    else:
        bought_something = buy_upgrades(detected)
        if bought_something:
            last_purchase_time = time.time()

    # 3. Клик по печеньке (выполняется всегда, если она найдена)
    if detected.get(CLASS_GAME):
        click_cookie(detected[CLASS_GAME][0], after_purchase=bought_something)
        return True

    return bought_something


# =====================================================================
#                              ГЛАВНЫЙ ЦИКЛ
# =====================================================================
def main():
    print("Запуск ИИ-автокликера с исправленным разбором координат.")
    print(f"Управление: Нажмите [{HOTKEY_PAUSE.upper()}], чтобы поставить бота на ПАУЗУ.")
    print("=======================================================\n")

    while True:
        if is_paused:
            time.sleep(PAUSED_POLL_DELAY)
            continue

        if not process_game():
            print("Ничего уверенно не найдено. Ожидание 1 сек...")
            time.sleep(IDLE_DELAY)


if __name__ == "__main__":
    main()

from ultralytics import YOLO

# 1. Автоматически находим корень проекта (на один уровень выше, чем train.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Формируем безопасные пути
CONFIG_PATH = BASE_DIR / "yaml n py" / "data.yaml"
MODEL_PATH = BASE_DIR / "yolov8n.pt"  # веса в корне

if __name__ == '__main__':
    # 1. Загрузка предобученной модели
    model = YOLO(str(MODEL_PATH))

    # 2. Запуск обучения
    results = model.train(
        data="data.yaml",
        epochs=200,          # количество эпох
        imgsz=640,           # размер изображения
        batch=32,
        workers=0,           # отключаем многопоточную (много проблем с этой фигней)
        name="cookie_detector",
        copy_paste=0.3,
        cls=0.5,
        patience=20          # остановка, если нет улучшений 50 эпох подряд
    )
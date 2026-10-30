import os
import random
import shutil
from pathlib import Path

# === НАСТРОЙКИ ===
# Скрипт сам находит папку, в которой лежит
BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
LABELS_DIR = BASE_DIR / "labels"

# Расширения картинок, которые ищем внутри папки labels
IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Соотношение (80% на train)
TRAIN_RATIO = 0.8
# =================


def main():
    print(f"Ищу все исходные файлы в папке: {LABELS_DIR}\n")

    # 1. Проверяем существование исходной папки labels
    if not LABELS_DIR.exists():
        print(f"ОШИБКА: Папка 'labels' не найдена по пути: {LABELS_DIR}")
        return

    # 2. Создаем структуру папок, если её еще нет
    train_img_dir = IMAGES_DIR / "train"
    val_img_dir = IMAGES_DIR / "val"
    train_lbl_dir = LABELS_DIR / "train"
    val_lbl_dir = LABELS_DIR / "val"

    for folder in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    # 3. Собираем пары (картинка + txt) ИЗ ПАПКИ LABELS
    # Ищем файлы только в корне папки labels, не заходя в создаваемые подпапки train/val
    all_files_in_labels = [f for f in LABELS_DIR.iterdir() if f.is_file()]

    # Фильтруем только картинки
    all_images = [
        f for f in all_files_in_labels if f.suffix.lower() in IMG_EXTENSIONS
    ]

    valid_pairs = []
    missing_txt_count = 0

    for img_path in all_images:
        txt_path = LABELS_DIR / f"{img_path.stem}.txt"
        if txt_path.exists():
            valid_pairs.append((img_path, txt_path))
        else:
            missing_txt_count += 1

    if missing_txt_count > 0:
        print(
            f"Предупреждение: Найдено {missing_txt_count} картинок без соответствующих .txt файлов. Они пропущены."
        )

    if not valid_pairs:
        print(
            f"ОШИБКА: В корне папки {LABELS_DIR} не найдено пар (Картинка + .txt файл)!"
        )
        print(
            "Убедитесь, что исходные картинки и текст-файлы лежат прямо в ней."
        )
        return

    print(f"Успешно обнаружено пар для разделения: {len(valid_pairs)}")

    # 4. Перемешиваем файлы для случайного распределения
    random.seed(42)
    random.shuffle(valid_pairs)

    # 5. Считаем точку разделения (80%)
    split_index = int(len(valid_pairs) * TRAIN_RATIO)
    train_pairs = valid_pairs[:split_index]
    val_pairs = valid_pairs[split_index:]

    # 6. Распределяем файлы
    print("\nКопируем 80% датасета в папки TRAIN...")
    for img_path, txt_path in train_pairs:
        # Картинки идут в images/train
        shutil.copy(img_path, train_img_dir / img_path.name)
        # Текстовые файлы идут в labels/train
        shutil.copy(txt_path, train_lbl_dir / txt_path.name)

    print("Копируем 20% датасета в папки VAL...")
    for img_path, txt_path in val_pairs:
        # Картинки идут в images/val
        shutil.copy(img_path, val_img_dir / img_path.name)
        # Текстовые файлы идут в labels/val
        shutil.copy(txt_path, val_lbl_dir / txt_path.name)

    print("\n🎉 Готово! Все файлы разложены идеально:")
    print(f" -> Картинки в images/train и .txt в labels/train: {len(train_pairs)} пар")
    print(f" -> Картинки в images/val и .txt в labels/val: {len(val_pairs)} par")


if __name__ == "__main__":
    main()

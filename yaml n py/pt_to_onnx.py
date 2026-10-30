from ultralytics import YOLO

# Загружаем вашу новую обученную на несколько классов модель
model = YOLO("./runs/detect/cookie_detector-6/weights/best.pt")
model.export(format="onnx", opset=12, simplify=True)

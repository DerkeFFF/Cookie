import torch
print("CUDA доступна:", torch.cuda.is_available())
print("Название видеокарты:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Нет GPU")

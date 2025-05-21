
# Cách đơn giản nhất để test YOLOv8 model

from ultralytics import YOLO
import matplotlib.pyplot as plt
from PIL import Image

# 1. Load model đã train
model = YOLO(
    'D:/Ky2nam4/Phantichthietkekientruchethong/BTL/modeldownload/best.pt')

# 2. Test nhanh trên 1 ảnh
# Thay đổi đường dẫn phù hợp
image_path = 'D:/Ky2nam4/Phantichthietkekientruchethong/Recognition/static/detection_images/detection_29_1747064228.jpg'
results = model.predict(image_path, save=True,
                        conf=0.01, iou=0.45, verbose=False)

# 4. Lấy ảnh kết quả và hiển thị với matplotlib
annotated_image = results[0].plot()
plt.figure(figsize=(10, 10))
plt.imshow(annotated_image)
plt.axis('off')
plt.show()

# 5. In thông tin detection
for result in results:
    boxes = result.boxes
    for box in boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = model.names[class_id]
        print(f"Detected: {class_name} with confidence {confidence:.2f}")

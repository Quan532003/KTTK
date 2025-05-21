import os
import logging

# Ví dụ: YOLOv8n.pt hoặc đường dẫn đến mô hình của bạn
YOLO_MODEL_PATH = "D:/Ky2nam4/Phantichthietkekientruchethong/Recognition/modeldownload/best.pt"

# Khai báo biến global để lưu trữ mô hình YOLOv8 (tải một lần, sử dụng nhiều lần)
yolo_model = None


def load_yolo_model():
    """
    Tải mô hình YOLO
    """
    global yolo_model

    if yolo_model is None:
        try:
            from ultralytics import YOLO

            # Kiểm tra xem file mô hình có tồn tại không
            if not os.path.exists(YOLO_MODEL_PATH):
                logging.error(
                    f"Không tìm thấy file mô hình tại: {YOLO_MODEL_PATH}")
                return None

            # Tải mô hình
            yolo_model = YOLO(YOLO_MODEL_PATH)
            logging.info(f"Đã tải mô hình YOLOv8 từ: {YOLO_MODEL_PATH}")

        except Exception as e:
            logging.error(f"Lỗi khi tải mô hình YOLOv8: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return None

    return yolo_model


def map_to_custom_label(original_label, y_position):
    """
    Chuyển đổi nhãn gốc từ YOLOv8 sang nhãn tùy chỉnh

    Args:
        original_label: Nhãn gốc từ mô hình YOLOv8
        y_position: Vị trí y của đối tượng (tương đối từ 0-1)

    Returns:
        str: Nhãn tùy chỉnh
    """
    # Chuyển đổi các nhãn phổ biến
    if original_label in ["cell phone", "smartphone", "mobile phone", "phone"]:
        return "phone"
    elif original_label == "person":
        if y_position < 0.4:  # Nếu đối tượng ở phía trên ảnh
            return "huitou"  # Nhìn sang bài người khác
        else:
            return "normal"  # Trạng thái bình thường
    elif original_label in ["book", "laptop", "notebook"]:
        return "zuobi"  # Sử dụng tài liệu trái phép
    else:
        return original_label  # Giữ nguyên nhãn gốc cho các trường hợp khác


def map_to_vietnamese_label(label):
    """
    Chuyển đổi 4 nhãn chính sang tiếng Việt dễ hiểu
    """
    label_map = {
        'normal': 'Bình thường',
        'phone': 'Sử dụng điện thoại',
        'huitou': 'Nhìn sang bài',
        'zuobi': 'Gian lận'
    }
    return label_map.get(label, label)

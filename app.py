from flask import Flask, render_template, redirect, url_for, jsonify, request
from config.config import Config
from datetime import datetime
import os
import base64
from PIL import Image
import io
import numpy as np
import time

# Import các DAOs
from dao.model_dao import ModelDAO
from dao.phase_detection_dao import PhaseDetectionDAO
from dao.detect_result_dao import DetectResultDAO
from utils.yolo_utils import load_yolo_model, map_to_vietnamese_label, map_to_custom_label

# Khởi tạo Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "8f42a73054b92c79c07935be5a17aa0ca383b783e4e321f3"

# Khởi tạo các DAO
model_dao = ModelDAO()
phase_detection_dao = PhaseDetectionDAO()
detect_result_dao = DetectResultDAO()


@app.template_filter('fix_image_path')
def fix_image_path(path):
    """Chuyển đổi backslash thành forward slash trong đường dẫn"""
    if path:
        # Xử lý các trường hợp đặc biệt
        if '\\' in path:
            path = path.replace('\\', '/')

        # Đảm bảo path bắt đầu bằng /static nếu là đường dẫn tương đối
        if path.startswith('static/'):
            path = '/' + path
        elif not path.startswith('/static/') and 'static/' in path:
            # Nếu path chứa static/ nhưng không bắt đầu bằng nó
            idx = path.find('static/')
            path = '/' + path[idx:]

        return path
    return path


@app.route('/')
def index():
    return redirect("/model-management")


@app.route('/model-management')
def model_management():
    model_list = model_dao.get_all()
    model_dict = []
    for i in range(len(model_list)-1, -1, -1):
        model_dict.append(model_list[i].to_dict())
    return render_template('model_management.html', models=model_dict)


@app.route('/recognition')
def recognition():
    models = model_dao.get_all()
    models_dict = [model.to_dict() for model in models]
    return render_template('recognition.html',
                           models=models_dict,
                           active_page='recognition')


@app.route('/api/phase_detection/start', methods=['POST'])
def start_phase_detection():
    try:
        data = request.json
        model_id = data.get('modelId')
        description = data.get('description', 'Phát hiện qua camera')
        print(data)
        model = model_dao.get_by_id(model_id)
        if not model:
            return jsonify({'success': False, 'message': 'Không tìm thấy mô hình'})

        if load_yolo_model() is None:
            return jsonify({'success': False, 'message': 'Không thể tải mô hình YOLOv8'})

        from models.phase_detection import PhaseDetection
        phase = PhaseDetection(
            description=description,
            timeDetect=datetime.now(),
            model=model
        )

        phase_id = phase_detection_dao.create(phase)

        detection_dir = os.path.join('static', 'detection_images')
        os.makedirs(detection_dir, exist_ok=True)
        return jsonify({
            'success': True,
            'phaseId': phase_id,
            'message': 'Đã bắt đầu phiên phát hiện mới'
        })
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})


@app.route('/api/phase_detection/stop', methods=['POST'])
def stop_phase_detection():
    try:
        data = request.json
        phase_id = data.get('phaseId')

        if not phase_id:
            return jsonify({'success': False, 'message': 'Thiếu ID phiên phát hiện'})

        phase = phase_detection_dao.get_by_id(phase_id)
        if not phase:
            return jsonify({'success': False, 'message': 'Không tìm thấy phiên phát hiện'})

        return jsonify({
            'success': True,
            'message': 'Đã kết thúc phiên phát hiện'
        })
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})


@app.route('/api/phase_detection/detect', methods=['POST'])
def detect_objects():
    try:
        data = request.json
        phase_id = data.get('phaseId')
        image_data = data.get('imageData')
        # Mặc định giá trị confidence rất thấp để hiển thị gần như tất cả các phát hiện
        confidence_threshold = data.get('confidence', 0.01)

        if not phase_id or not image_data:
            return jsonify({'success': False, 'message': 'Thiếu thông tin cần thiết'})

        phase = phase_detection_dao.get_by_id(phase_id)
        if not phase:
            return jsonify({'success': False, 'message': 'Không tìm thấy phiên phát hiện'})

        model = load_yolo_model()
        if model is None:
            return jsonify({'success': False, 'message': 'Không thể tải mô hình YOLOv8'})

        # Xử lý dữ liệu ảnh từ base64
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)

        # Lưu ảnh tạm thời để phát hiện
        detection_dir = os.path.join("static", "detection_images")
        os.makedirs(detection_dir, exist_ok=True)
        image_filename = f"detection_{phase_id}_{int(time.time())}.jpg"
        image_path = os.path.join(detection_dir, image_filename)

        with open(image_path, 'wb') as f:
            f.write(image_bytes)

        db_image_path = image_path.replace('\\', '/')

        results = model.predict(
            image_path, conf=0.15, iou=0.45, verbose=False)

        # Lấy kết quả phát hiện
        detections = []
        fraud_list = []

        for r in results:
            boxes = r.boxes
            # In tổng số phát hiện để debug
            print(f"Tổng số phát hiện: {len(boxes)}")

            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                # Chia cho chiều rộng ảnh gốc
                x_center = ((x1 + x2) / 2) / r.orig_shape[1]
                # Chia cho chiều cao ảnh gốc
                y_center = ((y1 + y2) / 2) / r.orig_shape[0]
                width = (x2 - x1) / r.orig_shape[1]
                height = (y2 - y1) / r.orig_shape[0]

                clsId = int(box.cls[0])
                confidence = float(box.conf[0])

                # Lấy nhãn từ model
                original_label = model.names[clsId]

                # In thông tin chi tiết về kết quả phát hiện
                print(
                    f"Class: {clsId}, Label: {original_label}, Confidence: {confidence:.4f}, Box: [{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}]")

                # Sử dụng hàm map_to_custom_label để ánh xạ nhãn
                # Tính vị trí tương đối theo chiều cao
                y_relative = y1 / r.orig_shape[0]
                label = map_to_custom_label(original_label, y_relative)
                print(f"{label}")

                # Chỉ giữ lại các nhãn trong tập đã xác định
                if label not in ['huitou', 'normal', 'phone', 'zuobi']:
                    label = 'normal'

                if label != 'normal':
                    fraud_list.append(label)

                display_label = map_to_vietnamese_label(label)

                detections.append({
                    'label': label,
                    'display_label': display_label,
                    'confidence': confidence,
                    'x': x_center,
                    'y': y_center,
                    'width': width,
                    'height': height,
                    'box': {
                        'x1': int(x1),
                        'y1': int(y1),
                        'x2': int(x2),
                        'y2': int(y2)
                    },
                    'class_id': clsId,
                    'original_label': original_label
                })

        # Sắp xếp detections theo độ tin cậy từ cao đến thấp
        detections.sort(key=lambda x: x['confidence'], reverse=True)

        # Tạo thông tin hiển thị
        detection_labels = [
            f"{d['display_label']} ({int(d['confidence']*100)}%)" for d in detections
        ]
        description = ", ".join(
            detection_labels) if detection_labels else "Không phát hiện hành vi gian lận"

        from models.detect_result import DetectResult
        from models.fraud import Fraud

        unique_frauds = list(set(fraud_list))
        fraud_objects = []
        for fraud_type in unique_frauds:
            fraud_obj = Fraud(fraud=fraud_type)
            fraud_objects.append(fraud_obj)

        result = DetectResult(
            description=description,
            imageUrl=db_image_path,
            phaseId=phase_id,
            frauds=fraud_objects
        )

        result_id = detect_result_dao.create(result)

        print(f"Tổng số phát hiện: {len(detections)}")
        print(f"Các loại gian lận phát hiện được: {unique_frauds}")

        return jsonify({
            'success': True,
            'resultId': result_id,
            'detections': detections,
            'message': 'Đã phát hiện đối tượng thành công',
            'image_path': db_image_path,
            'total_detections': len(detections)
        })
    except Exception as e:
        print(e)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})


@app.route('/detection-results/<int:phase_id>')
def view_detection_results(phase_id):
    try:
        from datetime import timedelta

        phase = phase_detection_dao.get_by_id(phase_id)
        if not phase:
            flash("Không tìm thấy phiên phát hiện!", "danger")
            return redirect(url_for('recognition'))

        return render_template('detection_results.html',
                               phase=phase,
                               timedelta=timedelta,
                               active_page='recognition')
    except Exception as e:
        print(e)
        return redirect(url_for('recognition'))


if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)

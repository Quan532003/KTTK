from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
import logging
import os
import base64
import io
import time
from PIL import Image
import numpy as np
from datetime import datetime
from utils.yolo_utils import load_yolo_model, map_to_vietnamese_label

detection_bp = Blueprint('detection', __name__)


@detection_bp.route('/recognition')
def recognition():
    models = current_app.model_dao.get_all()
    models_dict = [model.to_dict() for model in models]
    return render_template('recognition.html',
                           models=models_dict,
                           active_page='recognition')


@detection_bp.route('/api/phase_detection/start', methods=['POST'])
def start_phase_detection():
    try:
        data = request.json
        model_id = data.get('modelId')
        description = data.get('description', 'Phát hiện qua camera')

        model = current_app.model_dao.get_by_id(model_id)
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

        phase_id = current_app.phase_detection_dao.create(phase)

        detection_dir = os.path.join('static', 'detection_images')
        os.makedirs(detection_dir, exist_ok=True)

        return jsonify({
            'success': True,
            'phaseId': phase_id,
            'message': 'Đã bắt đầu phiên phát hiện mới'
        })
    except Exception as e:
        logging.error(f"Error in start_phase_detection: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})


@detection_bp.route('/api/phase_detection/stop', methods=['POST'])
def stop_phase_detection():
    try:
        data = request.json
        phase_id = data.get('phaseId')

        if not phase_id:
            return jsonify({'success': False, 'message': 'Thiếu ID phiên phát hiện'})

        phase = current_app.phase_detection_dao.get_by_id(phase_id)
        if not phase:
            return jsonify({'success': False, 'message': 'Không tìm thấy phiên phát hiện'})

        return jsonify({
            'success': True,
            'message': 'Đã kết thúc phiên phát hiện'
        })
    except Exception as e:
        logging.error(f"Error in stop_phase_detection: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})


@detection_bp.route('/api/phase_detection/detect', methods=['POST'])
def detect_objects():
    try:
        data = request.json
        phase_id = data.get('phaseId')
        image_data = data.get('imageData')
        confidence_threshold = data.get('confidence', 0.25)

        if not phase_id or not image_data:
            return jsonify({'success': False, 'message': 'Thiếu thông tin cần thiết'})

        phase = current_app.phase_detection_dao.get_by_id(phase_id)
        if not phase:
            return jsonify({'success': False, 'message': 'Không tìm thấy phiên phát hiện'})

        model = load_yolo_model()
        if model is None:
            return jsonify({'success': False, 'message': 'Không thể tải mô hình YOLOv8'})

        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)

        image = Image.open(io.BytesIO(image_bytes))
        image = image.resize((640, 640), Image.LANCZOS)
        img_np = np.array(image)

        detection_dir = os.path.join("static", "detection_images")
        os.makedirs(detection_dir, exist_ok=True)

        image_filename = f"detection_{phase_id}_{int(time.time())}.jpg"
        image_path = os.path.join(detection_dir, image_filename)
        image.save(image_path, quality=95)

        db_image_path = image_path.replace('\\', '/')

        results = model(img_np, conf=confidence_threshold,
                        iou=0.3, verbose=False)

        detections = []
        fraud_list = []

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                x_center = ((x1 + x2) / 2) / 640
                y_center = ((y1 + y2) / 2) / 640
                width = (x2 - x1) / 640
                height = (y2 - y1) / 640

                cls = int(box.cls[0])
                confidence = float(box.conf[0])

                label = model.names[cls] if cls in model.names else 'normal'

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
                    'class_id': cls
                })

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

        result_id = current_app.detect_result_dao.create(result)

        return jsonify({
            'success': True,
            'resultId': result_id,
            'detections': detections,
            'message': 'Đã phát hiện đối tượng thành công',
            'image_path': db_image_path
        })
    except Exception as e:
        logging.error(f"Error in detect_objects: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})


@detection_bp.route('/detection-results/<int:phase_id>')
def view_detection_results(phase_id):
    try:
        from datetime import timedelta

        phase = current_app.phase_detection_dao.get_by_id(phase_id)
        if not phase:
            flash("Không tìm thấy phiên phát hiện!", "danger")
            return redirect(url_for('detection.recognition'))

        return render_template('detection_results.html',
                               phase=phase,
                               timedelta=timedelta,
                               active_page='recognition')
    except Exception as e:
        logging.error(f"Error in view_detection_results: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        flash(f"Lỗi: {str(e)}", "danger")
        return redirect(url_for('detection.recognition'))


@detection_bp.route('/recognize-camera')
def recognize_camera():
    flash('Đã bắt đầu nhận dạng qua camera!', 'info')
    return redirect(url_for('detection.recognition') + '?mode=camera')


@detection_bp.route('/recognize-video')
def recognize_video():
    flash('Đã bắt đầu nhận dạng qua video!', 'info')
    return redirect(url_for('detection.recognition') + '?mode=video')

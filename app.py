import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

from config.config import Config
from utils.db_util import DatabaseUtil
from utils.enums import ModelType, TypeLabel

from models.model import Model
from models.train_info import TrainInfo
from models.training_data import TrainingData
from models.fraud_template import FraudTemplate
from models.fraud_label import FraudLabel
from models.bounding_box import BoundingBox
from models.training_lost import TrainingLost

from dao.model_dao import ModelDAO
from dao.train_info_dao import TrainInfoDAO
from dao.training_data_dao import TrainingDataDAO
from dao.fraud_template_dao import FraudTemplateDAO
from dao.fraud_label_dao import FraudLabelDAO
from dao.bounding_box_dao import BoundingBoxDAO
from dao.training_lost_dao import TrainingLostDAO

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.secret_key = "8f42a73054b92c79c07935be5a17aa0ca383b783e4e321f3"

model_dao = ModelDAO()
train_info_dao = TrainInfoDAO()
training_data_dao = TrainingDataDAO()
fraud_template_dao = FraudTemplateDAO()
fraud_label_dao = FraudLabelDAO()
bounding_box_dao = BoundingBoxDAO()
training_lost_dao = TrainingLostDAO()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return redirect(url_for('model_management'))


@app.route('/model-management')
def model_management():
    try:
        models = model_dao.get_all()
        models_dict = [model.to_dict() for model in models]
        return render_template('model_management.html', models=models_dict, active_page='model_management')
    except Exception as e:
        logging.error(f"Error in model_management route: {str(e)}")
        flash(f"Lỗi: {str(e)}", "danger")
        return render_template('model_management.html', models=[], active_page='model_management')


@app.route('/statistics')
def statistics():
    try:
        models = model_dao.get_all()
        total_models = len(models)
        total_mae = 0
        total_mse = 0
        total_accuracy = 0
        models_with_metrics = 0
        model_types = {}

        for model in models:
            model_type = model.modelType.value if isinstance(
                model.modelType, ModelType) else model.modelType
            if model_type in model_types:
                model_types[model_type] += 1
            else:
                model_types[model_type] = 1

            if model.trainInfo:
                models_with_metrics += 1

                if hasattr(model.trainInfo, 'mae') and model.trainInfo.mae is not None:
                    total_mae += float(model.trainInfo.mae)

                if hasattr(model.trainInfo, 'mse') and model.trainInfo.mse is not None:
                    total_mse += float(model.trainInfo.mse)

                if hasattr(model.trainInfo, 'accuracy') and model.trainInfo.accuracy is not None:
                    total_accuracy += float(model.trainInfo.accuracy)

        avg_mae = total_mae / models_with_metrics if models_with_metrics > 0 else 0
        avg_mse = total_mse / models_with_metrics if models_with_metrics > 0 else 0
        avg_accuracy = total_accuracy / models_with_metrics if models_with_metrics > 0 else 0

        model_names = [model.modelName for model in models]
        accuracies = [float(model.trainInfo.accuracy) if model.trainInfo and hasattr(
            model.trainInfo, 'accuracy') and model.trainInfo.accuracy is not None else 0 for model in models]
        maes = [float(model.trainInfo.mae) if model.trainInfo and hasattr(
            model.trainInfo, 'mae') and model.trainInfo.mae is not None else 0 for model in models]
        mses = [float(model.trainInfo.mse) if model.trainInfo and hasattr(
            model.trainInfo, 'mse') and model.trainInfo.mse is not None else 0 for model in models]

        accuracy_ranges = {
            '90-100%': 0,
            '80-90%': 0,
            '70-80%': 0,
            '60-70%': 0,
            'Dưới 60%': 0
        }

        for acc in accuracies:
            acc_percent = acc * 100
            if acc_percent >= 90:
                accuracy_ranges['90-100%'] += 1
            elif acc_percent >= 80:
                accuracy_ranges['80-90%'] += 1
            elif acc_percent >= 70:
                accuracy_ranges['70-80%'] += 1
            elif acc_percent >= 60:
                accuracy_ranges['60-70%'] += 1
            else:
                accuracy_ranges['Dưới 60%'] += 1

        return render_template('statistics.html',
                               total_models=total_models,
                               avg_mae=avg_mae,
                               avg_mse=avg_mse,
                               avg_accuracy=avg_accuracy,
                               model_types=model_types,
                               model_names=json.dumps(model_names),
                               accuracies=json.dumps(accuracies),
                               maes=json.dumps(maes),
                               mses=json.dumps(mses),
                               accuracy_ranges=accuracy_ranges,
                               active_page='statistics')
    except Exception as e:
        logging.error(f"Error in statistics route: {str(e)}")
        flash(f"Lỗi: {str(e)}", "danger")
        return render_template('statistics.html',
                               total_models=0,
                               avg_mae=0,
                               avg_mse=0,
                               avg_accuracy=0,
                               model_types={},
                               model_names=json.dumps([]),
                               accuracies=json.dumps([]),
                               maes=json.dumps([]),
                               mses=json.dumps([]),
                               accuracy_ranges={},
                               active_page='statistics')


@app.route('/recognition')
def recognition():
    models = model_dao.get_all()
    models_dict = [model.to_dict() for model in models]
    return render_template('recognition.html',
                           models=models_dict,
                           active_page='recognition')


@app.route('/add-model', methods=['GET', 'POST'])
def add_model():
    if request.method == 'POST':
        try:
            # Lấy dữ liệu từ form
            model_name = request.form['model_name']
            model_type = request.form['model_type']
            version = request.form['version']
            description = request.form.get('description', '')

            # Lấy các thông số huấn luyện
            epoch = int(request.form.get('epochs', Config.DEFAULT_EPOCH))
            batch_size = int(request.form.get(
                'batch_size', Config.DEFAULT_BATCH_SIZE))
            learning_rate = float(request.form.get(
                'learning_rate', Config.DEFAULT_LEARNING_RATE))

            # Kiểm tra các trường bắt buộc
            if not model_name or not model_type or not version:
                flash("Vui lòng điền đầy đủ thông tin bắt buộc.", "danger")
                return redirect(url_for('add_model'))

            # Kiểm tra xem mô hình đã tồn tại chưa
            existing_models = model_dao.get_all()
            for model in existing_models:
                if model.modelName == model_name and model.version == version:
                    flash(
                        f"Mô hình {model_name} phiên bản {version} đã tồn tại.", "danger")
                    return redirect(url_for('add_model'))

            # Xử lý tải lên file
            model_path = None
            config_path = None

            if 'model_file' in request.files:
                model_file = request.files['model_file']
                if model_file and model_file.filename and allowed_file(model_file.filename):
                    model_filename = secure_filename(model_file.filename)
                    model_path = os.path.join(
                        Config.UPLOAD_FOLDER, model_filename)
                    model_file.save(model_path)

            if 'config_file' in request.files:
                config_file = request.files['config_file']
                if config_file and config_file.filename and allowed_file(config_file.filename):
                    config_filename = secure_filename(config_file.filename)
                    config_path = os.path.join(
                        Config.UPLOAD_FOLDER, config_filename)
                    config_file.save(config_path)

            # Tạo đối tượng TrainInfo
            train_info = TrainInfo(
                epoch=epoch,
                learningRate=learning_rate,
                batchSize=batch_size,
                accuracy=float(request.form.get('accuracy', 0)),
                timeTrain=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                trainDuration=0  # Sẽ cập nhật sau khi huấn luyện
            )

            # Tạo đối tượng Model
            model = Model(
                modelName=model_name,
                modelType=model_type,
                version=version,
                description=description,
                lastUpdate=datetime.now(),
                trainInfo=train_info
            )

            # Lưu vào database
            model_id = model_dao.create(model)

            # Lưu mối quan hệ với FraudTemplate
            sample_images = request.form.getlist('sample_images[]')
            if sample_images:
                for image_id in sample_images:
                    template = fraud_template_dao.get_by_id(int(image_id))
                    if template:
                        training_data = TrainingData(
                            modelId=model_id,
                            fraudTemplateId=template.idTemplate,
                            description=f"Training data for {model_name}",
                            timeUpdate=datetime.now()
                        )
                        training_data_dao.create(training_data)

            flash('Thêm mô hình thành công!', 'success')
            return redirect(url_for('model_management'))
        except Exception as e:
            logging.error(f"Error in add_model route: {str(e)}")
            flash(f"Lỗi: {str(e)}", "danger")

    templates = fraud_template_dao.get_all()
    templates_dict = [template.to_dict() for template in templates]
    print(templates_dict)
    return render_template('add_model.html',
                           sample_images=templates_dict,
                           model_types=ModelType.get_all_values(),
                           active_page='model_management')


@app.route('/edit-model/<int:id>', methods=['GET', 'POST'])
def edit_model(id):
    # Lấy thông tin mô hình
    model = model_dao.get_by_id(id)

    if not model:
        flash("Không tìm thấy mô hình!", "danger")
        return redirect(url_for('model_management'))

    if request.method == 'POST':
        try:
            model_name = request.form['model_name']
            model_type = request.form['model_type']
            version = request.form['version']
            description = request.form.get('description', '')

            model.modelName = model_name
            model.modelType = model_type
            model.version = version
            model.description = description
            model.lastUpdate = datetime.now()

            if model.trainInfo:
                model.trainInfo.accuracy = float(
                    request.form.get('accuracy', model.trainInfo.accuracy))
                if hasattr(model.trainInfo, 'precision'):
                    model.trainInfo.precision = float(
                        request.form.get('precision', model.trainInfo.precision))
                if hasattr(model.trainInfo, 'recall'):
                    model.trainInfo.recall = float(
                        request.form.get('recall', model.trainInfo.recall))
                if hasattr(model.trainInfo, 'f1_score'):
                    model.trainInfo.f1_score = float(
                        request.form.get('f1_score', model.trainInfo.f1_score))

            model_dao.update(model)

            flash('Cập nhật mô hình thành công!', 'success')
            return redirect(url_for('model_management'))
        except Exception as e:
            logging.error(f"Error in edit_model route: {str(e)}")
            flash(f"Lỗi: {str(e)}", "danger")

    model_dict = model.to_dict()

    training_data_list = training_data_dao.get_by_model_id(id)
    used_templates = [td.fraudTemplateId for td in training_data_list]

    templates = fraud_template_dao.get_all()
    templates_dict = [template.to_dict() for template in templates]

    return render_template('edit_model.html',
                           model=model_dict,
                           sample_images=templates_dict,
                           used_templates=used_templates,
                           model_types=ModelType.get_all_values(),
                           active_page='model_management')


@app.route('/delete-model/<int:id>', methods=['POST'])
def delete_model(id):
    try:
        model = model_dao.get_by_id(id)
        if not model:
            flash("Không tìm thấy mô hình!", "danger")
            return redirect(url_for('model_management'))

        training_data_dao.delete_by_model_id(id)

        model_dao.delete(id)

        flash('Xóa mô hình thành công!', 'success')
    except Exception as e:
        logging.error(f"Error in delete_model route: {str(e)}")
        flash(f"Lỗi: {str(e)}", "danger")

    return redirect(url_for('model_management'))


@app.route('/api/train', methods=['POST'])
def api_train():
    try:
        data = request.json

        # Lấy thông tin mô hình
        model_id = data.get('model_id')

        # Kiểm tra xem mô hình có tồn tại không
        model = model_dao.get_by_id(model_id)
        if not model:
            return jsonify({'success': False, 'message': 'Không tìm thấy mô hình'})

        # Lấy thông số huấn luyện
        epochs = data.get('epochs', 100)
        batch_size = data.get('batch_size', 16)
        learning_rate = data.get('learning_rate', 0.001)

        # Giả lập quá trình huấn luyện - trả về kết quả thành công
        # Trong thực tế, bạn sẽ khởi động một quy trình huấn luyện thực sự

        # Cập nhật thông tin huấn luyện
        if model.trainInfo:
            model.trainInfo.epoch = epochs
            model.trainInfo.batchSize = batch_size
            model.trainInfo.learningRate = learning_rate
            model.trainInfo.accuracy = 0.85
            if hasattr(model.trainInfo, 'precision'):
                model.trainInfo.precision = 0.83
            if hasattr(model.trainInfo, 'recall'):
                model.trainInfo.recall = 0.87
            if hasattr(model.trainInfo, 'f1_score'):
                model.trainInfo.f1_score = 0.85

            # Tạo dữ liệu giả về quá trình huấn luyện
            for epoch in range(1, epochs + 1, max(1, epochs // 10)):
                loss = 1.0 - (epoch / epochs) * 0.7
                training_lost = TrainingLost(
                    epoch=epoch,
                    lost=loss,
                    trainInfoId=model.trainInfo.idInfo
                )
                training_lost_dao.create(training_lost)

            # Cập nhật TrainInfo
            train_info_dao.update(model.trainInfo)

        # Cập nhật thời gian cập nhật cuối cùng của mô hình
        model.lastUpdate = datetime.now()
        model_dao.update(model)

        return jsonify({
            'success': True,
            'model_id': model_id,
            'accuracy': 0.85,
            'message': 'Huấn luyện thành công'
        })

    except Exception as e:
        logging.error(f"Error in api_train: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})


@app.route('/api/models', methods=['GET'])
def api_get_models():
    try:
        models = model_dao.get_all()
        return jsonify([model.to_dict() for model in models])
    except Exception as e:
        logging.error(f"Error in api_get_models: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/models/<int:id>', methods=['GET'])
def api_get_model(id):
    try:
        model = model_dao.get_by_id(id)
        if not model:
            return jsonify({'error': 'Model not found'}), 404
        return jsonify(model.to_dict())
    except Exception as e:
        logging.error(f"Error in api_get_model: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/templates', methods=['GET'])
def api_get_templates():
    try:
        templates = fraud_template_dao.get_all()
        return jsonify([template.to_dict() for template in templates])
    except Exception as e:
        logging.error(f"Error in api_get_templates: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/recognize-camera')
def recognize_camera():
    # Đây là chức năng giả lập
    flash('Đã bắt đầu nhận dạng qua camera!', 'info')
    return redirect(url_for('recognition') + '?mode=camera')


@app.route('/recognize-video')
def recognize_video():
    # Đây là chức năng giả lập
    flash('Đã bắt đầu nhận dạng qua video!', 'info')
    return redirect(url_for('recognition') + '?mode=video')

# Khởi tạo database khi server khởi động


with app.app_context():
    try:
        # Khởi tạo database từ file schema
        db_util = DatabaseUtil()
        db_util.initialize_database('schema.sql')
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing database: {str(e)}")

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)

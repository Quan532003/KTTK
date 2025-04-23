from datetime import datetime
from utils.enums import ModelType
from .train_info import TrainInfo


class Model:
    """
    Đại diện cho một mô hình YOLO
    """

    def __init__(self, idModel=None, modelName=None, modelType=None, version=None,
                 description=None, lastUpdate=None, trainInfo=None):
        """
        Khởi tạo một đối tượng Model mới

        Args:
            idModel (int, optional): ID của mô hình
            modelName (str, optional): Tên của mô hình
            modelType (ModelType, optional): Loại mô hình
            version (str, optional): Phiên bản mô hình
            description (str, optional): Mô tả về mô hình
            lastUpdate (datetime, optional): Thời gian cập nhật cuối cùng
            trainInfo (TrainInfo, optional): Thông tin huấn luyện
        """
        self.idModel = idModel
        self.modelName = modelName
        self.modelType = modelType
        self.version = version
        self.description = description
        self.lastUpdate = lastUpdate if lastUpdate else datetime.now()
        self.trainInfo = trainInfo

    def get_fraud_templates(self):
        """
        Lấy danh sách các fraud template liên quan đến mô hình

        Returns:
            list: Danh sách các FraudTemplate
        """
        # Phương thức này sẽ được thực hiện bởi DAO
        pass

    def get_train_info(self):
        """
        Lấy thông tin huấn luyện của mô hình

        Returns:
            TrainInfo: Đối tượng TrainInfo liên kết với mô hình
        """
        # Phương thức này sẽ được thực hiện bởi DAO
        return self.trainInfo

    def to_dict(self):
        """
        Chuyển đổi đối tượng thành dictionary

        Returns:
            dict: Dictionary chứa thông tin của đối tượng
        """
        model_dict = {
            'idModel': self.idModel,
            'modelName': self.modelName,
            'modelType': self.modelType.value if isinstance(self.modelType, ModelType) else self.modelType,
            'version': self.version,
            'description': self.description,
            'lastUpdate': self.lastUpdate.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.lastUpdate, datetime) else self.lastUpdate,
            'accuracy': self.trainInfo.accuracy
        }

        if self.trainInfo:
            model_dict['trainInfo'] = self.trainInfo.to_dict() if hasattr(
                self.trainInfo, 'to_dict') else self.trainInfo

        return model_dict

    @classmethod
    def from_dict(cls, data):
        """
        Tạo đối tượng từ dictionary

        Args:
            data (dict): Dictionary chứa thông tin đối tượng

        Returns:
            Model: Đối tượng Model mới
        """
        model = cls()

        model.idModel = data.get('idModel')
        model.modelName = data.get('modelName')

        model_type = data.get('modelType')
        if model_type:
            try:
                model.modelType = ModelType(model_type)
            except ValueError:
                model.modelType = model_type

        model.version = data.get('version')
        model.description = data.get('description')

        last_update = data.get('lastUpdate')
        if last_update and isinstance(last_update, str):
            try:
                model.lastUpdate = datetime.strptime(
                    last_update, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                model.lastUpdate = last_update
        else:
            model.lastUpdate = last_update

        train_info_data = data.get('trainInfo')
        if train_info_data:
            if isinstance(train_info_data, dict):
                model.trainInfo = TrainInfo.from_dict(train_info_data)
            else:
                model.trainInfo = train_info_data

        return model

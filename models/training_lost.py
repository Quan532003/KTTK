class TrainingLost:
    """
    Đại diện cho thông tin mất mát trong quá trình huấn luyện
    """
    def __init__(self, idTrainingLost=None, epoch=None, lost=None, trainInfoId=None):
        """
        Khởi tạo một đối tượng TrainingLost mới
        
        Args:
            idTrainingLost (int, optional): ID của thông tin mất mát
            epoch (int, optional): Epoch tương ứng
            lost (float, optional): Giá trị mất mát
            trainInfoId (int, optional): ID của TrainInfo liên kết
        """
        self.idTrainingLost = idTrainingLost
        self.epoch = epoch
        self.lost = lost
        self.trainInfoId = trainInfoId
    
    def to_dict(self):
        """
        Chuyển đổi đối tượng thành dictionary
        
        Returns:
            dict: Dictionary chứa thông tin của đối tượng
        """
        return {
            'idTrainingLost': self.idTrainingLost,
            'epoch': self.epoch,
            'lost': self.lost,
            'trainInfoId': self.trainInfoId
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Tạo đối tượng từ dictionary
        
        Args:
            data (dict): Dictionary chứa thông tin đối tượng
            
        Returns:
            TrainingLost: Đối tượng TrainingLost mới
        """
        training_lost = cls()
        
        training_lost.idTrainingLost = data.get('idTrainingLost')
        training_lost.epoch = data.get('epoch')
        training_lost.lost = data.get('lost')
        training_lost.trainInfoId = data.get('trainInfoId')
            
        return training_lost
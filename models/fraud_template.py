from datetime import datetime


class FraudTemplate:
    def __init__(self, idTemplate=None, description=None, imageUrl=None, timeUpdate=None, labels=None, boundingboxs=None):
        self.idTemplate = idTemplate
        self.description = description
        self.imageUrl = imageUrl
        self.timeUpdate = timeUpdate if timeUpdate else datetime.now()
        self.labels = labels if labels else []
        self.boundingBox = boundingboxs if boundingboxs else []

    def to_dict(self):
        template_dict = {
            'idTemplate': self.idTemplate,
            'description': self.description,
            'imageUrl': self.imageUrl,
            'timeUpdate': self.timeUpdate.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.timeUpdate, datetime) else self.timeUpdate
        }
        return template_dict

    @classmethod
    def from_dict(cls, data):
        from .fraud_label import FraudLabel

        template = cls()

        template.idTemplate = data.get('idTemplate')
        template.description = data.get('description')
        template.imageUrl = data.get('imageUrl')

        time_update = data.get('timeUpdate')
        if time_update and isinstance(time_update, str):
            try:
                template.timeUpdate = datetime.strptime(
                    time_update, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                template.timeUpdate = time_update
        else:
            template.timeUpdate = time_update
        return template

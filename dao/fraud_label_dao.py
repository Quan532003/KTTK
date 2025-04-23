import logging
from utils.db_util import DatabaseUtil
from models.fraud_label import FraudLabel
from utils.enums import TypeLabel


class FraudLabelDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = "SELECT * FROM FraudLabel"

            rows = self.db_util.execute_query(query, fetchall=True)

            labels = []
            for row in rows:
                label = FraudLabel(
                    idLabel=row['idLabel'],
                    description=row['description'],
                    typeLabel=row['typeLabel'],
                )
                labels.append(label)

            return labels
        except Exception as e:
            logging.error(f"Error in FraudLabelDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, label_id):
        try:
            query = "SELECT * FROM FraudLabel WHERE idLabel = %s"

            row = self.db_util.execute_query(query, (label_id,), fetchone=True)

            if not row:
                return None

            label = FraudLabel(
                idLabel=row['idLabel'],
                description=row['description'],
                typeLabel=row['typeLabel']
            )
            return label
        except Exception as e:
            logging.error(f"Error in FraudLabelDAO.get_by_id: {str(e)}")
            raise

    def get_by_template_id(self, template_id):
        try:
            query = "SELECT * FROM FraudLabel WHERE fraudTemplateId = %s"

            rows = self.db_util.execute_query(
                query, (template_id,), fetchall=True)

            labels = []
            for row in rows:
                label = FraudLabel(
                    idLabel=row['idLabel'],
                    description=row['description'],
                    typeLabel=row['typeLabel'],
                    fraudTemplateId=row['fraudTemplateId']
                )

                # Lấy danh sách BoundingBox
                from dao.bounding_box_dao import BoundingBoxDAO
                bounding_box_dao = BoundingBoxDAO()
                label.boundingBoxList = bounding_box_dao.get_by_label_id(
                    row['idLabel'])

                labels.append(label)

            return labels
        except Exception as e:
            logging.error(
                f"Error in FraudLabelDAO.get_by_template_id: {str(e)}")
            raise

    def create(self, label):
        try:
            query = """
                INSERT INTO FraudLabel (description, typeLabel, fraudTemplateId)
                VALUES (%s, %s, %s)
            """
            type_label = label.typeLabel.value if isinstance(
                label.typeLabel, TypeLabel) else label.typeLabel

            params = (
                label.description,
                type_label,
                label.fraudTemplateId
            )

            label_id = self.db_util.execute_query(query, params, commit=True)

            # Lưu các BoundingBox nếu có
            if label.boundingBoxList:
                from dao.bounding_box_dao import BoundingBoxDAO
                bounding_box_dao = BoundingBoxDAO()

                for box in label.boundingBoxList:
                    box.fraudLabelId = label_id
                    # Gán đối tượng label để có thể sử dụng trong BoundingBox
                    box.fraudLabel = label

                    # Đảm bảo có fraudTemplateId cho BoundingBox
                    if not box.fraudTemplateId:
                        box.fraudTemplateId = label.fraudTemplateId

                    # Đảm bảo có fraudTemplate cho BoundingBox
                    if not box.fraudTemplate and label.fraudTemplate:
                        box.fraudTemplate = label.fraudTemplate

                    bounding_box_dao.create(box)

            return label_id
        except Exception as e:
            logging.error(f"Error in FraudLabelDAO.create: {str(e)}")
            raise

    def update(self, label):
        try:
            query = """
                UPDATE FraudLabel
                SET description = %s, typeLabel = %s, fraudTemplateId = %s
                WHERE idLabel = %s
            """

            type_label = label.typeLabel.value if isinstance(
                label.typeLabel, TypeLabel) else label.typeLabel

            params = (
                label.description,
                type_label,
                label.fraudTemplateId,
                label.idLabel
            )

            self.db_util.execute_query(query, params, commit=True)

            # Cập nhật các BoundingBox
            if label.boundingBoxList:
                from dao.bounding_box_dao import BoundingBoxDAO
                bounding_box_dao = BoundingBoxDAO()

                # Xóa tất cả các BoundingBox cũ
                bounding_box_dao.delete_by_label_id(label.idLabel)

                # Tạo lại các BoundingBox mới
                for box in label.boundingBoxList:
                    box.fraudLabelId = label.idLabel
                    # Gán đối tượng label để có thể sử dụng trong BoundingBox
                    box.fraudLabel = label

                    # Đảm bảo có fraudTemplateId cho BoundingBox
                    if not box.fraudTemplateId:
                        box.fraudTemplateId = label.fraudTemplateId

                    # Đảm bảo có fraudTemplate cho BoundingBox
                    if not box.fraudTemplate and label.fraudTemplate:
                        box.fraudTemplate = label.fraudTemplate

                    bounding_box_dao.create(box)

            return True
        except Exception as e:
            logging.error(f"Error in FraudLabelDAO.update: {str(e)}")
            raise

    def delete(self, label_id):
        try:
            # Xóa tất cả các BoundingBox liên quan
            from dao.bounding_box_dao import BoundingBoxDAO
            bounding_box_dao = BoundingBoxDAO()
            bounding_box_dao.delete_by_label_id(label_id)

            # Xóa FraudLabel
            query = "DELETE FROM FraudLabel WHERE idLabel = %s"
            self.db_util.execute_query(query, (label_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in FraudLabelDAO.delete: {str(e)}")
            raise

    def delete_by_template_id(self, template_id):
        try:
            # Lấy tất cả các FraudLabel để xóa BoundingBox
            labels = self.get_by_template_id(template_id)

            # Xóa tất cả các BoundingBox liên quan đến các FraudLabel
            from dao.bounding_box_dao import BoundingBoxDAO
            bounding_box_dao = BoundingBoxDAO()
            for label in labels:
                bounding_box_dao.delete_by_label_id(label.idLabel)

            # Xóa tất cả các FraudLabel
            query = "DELETE FROM FraudLabel WHERE fraudTemplateId = %s"
            self.db_util.execute_query(query, (template_id,), commit=True)

            return True
        except Exception as e:
            logging.error(
                f"Error in FraudLabelDAO.delete_by_template_id: {str(e)}")
            raise

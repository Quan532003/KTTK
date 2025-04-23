import logging
from utils.db_util import DatabaseUtil
from models.bounding_box import BoundingBox


class BoundingBoxDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        try:
            query = """
                SELECT bb.*, fl.idLabel as fraudLabelId, ft.idTemplate as fraudTemplateId
                FROM BoundingBox bb
                JOIN FraudLabel fl ON bb.fraudLabelId = fl.idLabel
                JOIN FraudTemplate ft ON bb.fraudTemplateId = ft.idTemplate
            """

            rows = self.db_util.execute_query(query, fetchall=True)

            boxes = []
            for row in rows:
                box = BoundingBox(
                    idBox=row['idBox'],
                    xCenter=row['xCenter'],
                    yCenter=row['yCenter'],
                    width=row['width'],
                    height=row['height'],
                    xPixel=row['xPixel'],
                    yPixel=row['yPixel'],
                    widthPixel=row['widthPixel'],
                    heightPixel=row['heightPixel'],
                    fraudTemplateId=row['fraudTemplateId'],
                    fraudLabelId=row['fraudLabelId']
                )

                # Lấy đối tượng FraudTemplate và FraudLabel
                from dao.fraud_template_dao import FraudTemplateDAO
                from dao.fraud_label_dao import FraudLabelDAO

                fraud_template_dao = FraudTemplateDAO()
                fraud_label_dao = FraudLabelDAO()

                box.fraudTemplate = fraud_template_dao.get_by_id(
                    row['fraudTemplateId'])
                box.fraudLabel = fraud_label_dao.get_by_id(row['fraudLabelId'])

                boxes.append(box)

            return boxes
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, box_id):
        try:
            query = """
                SELECT bb.*, fl.idLabel as fraudLabelId, ft.idTemplate as fraudTemplateId
                FROM BoundingBox bb
                JOIN FraudLabel fl ON bb.fraudLabelId = fl.idLabel
                JOIN FraudTemplate ft ON bb.fraudTemplateId = ft.idTemplate
                WHERE bb.idBox = %s
            """

            row = self.db_util.execute_query(query, (box_id,), fetchone=True)

            if not row:
                return None

            box = BoundingBox(
                idBox=row['idBox'],
                xCenter=row['xCenter'],
                yCenter=row['yCenter'],
                width=row['width'],
                height=row['height'],
                xPixel=row['xPixel'],
                yPixel=row['yPixel'],
                widthPixel=row['widthPixel'],
                heightPixel=row['heightPixel'],
                fraudTemplateId=row['fraudTemplateId'],
                fraudLabelId=row['fraudLabelId']
            )

            # Lấy đối tượng FraudTemplate và FraudLabel
            from dao.fraud_template_dao import FraudTemplateDAO
            from dao.fraud_label_dao import FraudLabelDAO

            fraud_template_dao = FraudTemplateDAO()
            fraud_label_dao = FraudLabelDAO()

            box.fraudTemplate = fraud_template_dao.get_by_id(
                row['fraudTemplateId'])
            box.fraudLabel = fraud_label_dao.get_by_id(row['fraudLabelId'])

            return box
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.get_by_id: {str(e)}")
            raise

    def get_by_label_id(self, label_id):
        """
        Lấy tất cả các bounding box theo FraudLabel ID

        Args:
            label_id (int): ID của FraudLabel

        Returns:
            list: Danh sách các đối tượng BoundingBox
        """
        try:
            query = """
                SELECT bb.*, fl.idLabel as fraudLabelId, ft.idTemplate as fraudTemplateId
                FROM BoundingBox bb
                JOIN FraudLabel fl ON bb.fraudLabelId = fl.idLabel
                JOIN FraudTemplate ft ON bb.fraudTemplateId = ft.idTemplate
                WHERE bb.fraudLabelId = %s
            """

            rows = self.db_util.execute_query(
                query, (label_id,), fetchall=True)

            boxes = []
            for row in rows:
                box = BoundingBox(
                    idBox=row['idBox'],
                    xCenter=row['xCenter'],
                    yCenter=row['yCenter'],
                    width=row['width'],
                    height=row['height'],
                    xPixel=row['xPixel'],
                    yPixel=row['yPixel'],
                    widthPixel=row['widthPixel'],
                    heightPixel=row['heightPixel'],
                    fraudTemplateId=row['fraudTemplateId'],
                    fraudLabelId=row['fraudLabelId']
                )

                # Lấy đối tượng FraudTemplate và FraudLabel
                from dao.fraud_template_dao import FraudTemplateDAO

                fraud_template_dao = FraudTemplateDAO()
                box.fraudTemplate = fraud_template_dao.get_by_id(
                    row['fraudTemplateId'])

                # FraudLabel sẽ được set sau để tránh vòng lặp vô hạn

                boxes.append(box)

            return boxes
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.get_by_label_id: {str(e)}")
            raise

    def get_by_template_id(self, template_id):
        """
        Lấy tất cả các bounding box theo FraudTemplate ID

        Args:
            template_id (int): ID của FraudTemplate

        Returns:
            list: Danh sách các đối tượng BoundingBox
        """
        try:
            query = """
                SELECT bb.*, fl.idLabel as fraudLabelId, ft.idTemplate as fraudTemplateId
                FROM BoundingBox bb
                JOIN FraudLabel fl ON bb.fraudLabelId = fl.idLabel
                JOIN FraudTemplate ft ON bb.fraudTemplateId = ft.idTemplate
                WHERE bb.fraudTemplateId = %s
            """

            rows = self.db_util.execute_query(
                query, (template_id,), fetchall=True)

            boxes = []
            for row in rows:
                box = BoundingBox(
                    idBox=row['idBox'],
                    xCenter=row['xCenter'],
                    yCenter=row['yCenter'],
                    width=row['width'],
                    height=row['height'],
                    xPixel=row['xPixel'],
                    yPixel=row['yPixel'],
                    widthPixel=row['widthPixel'],
                    heightPixel=row['heightPixel'],
                    fraudTemplateId=row['fraudTemplateId'],
                    fraudLabelId=row['fraudLabelId']
                )

                # Lấy đối tượng FraudLabel
                from dao.fraud_label_dao import FraudLabelDAO

                fraud_label_dao = FraudLabelDAO()
                box.fraudLabel = fraud_label_dao.get_by_id(row['fraudLabelId'])

                # FraudTemplate sẽ được set sau để tránh vòng lặp vô hạn

                boxes.append(box)

            return boxes
        except Exception as e:
            logging.error(
                f"Error in BoundingBoxDAO.get_by_template_id: {str(e)}")
            raise

    def create(self, box):
        """
        Tạo bounding box mới

        Args:
            box (BoundingBox): Đối tượng BoundingBox cần tạo

        Returns:
            int: ID của bounding box vừa tạo
        """
        try:
            query = """
                INSERT INTO BoundingBox (xCenter, yCenter, width, height, 
                                    xPixel, yPixel, widthPixel, heightPixel, 
                                    fraudTemplateId, fraudLabelId)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # Lấy ID của FraudTemplate và FraudLabel
            fraudTemplateId = box.fraudTemplateId
            if not fraudTemplateId and box.fraudTemplate and hasattr(box.fraudTemplate, 'idTemplate'):
                fraudTemplateId = box.fraudTemplate.idTemplate

            fraudLabelId = box.fraudLabelId
            if not fraudLabelId and box.fraudLabel and hasattr(box.fraudLabel, 'idLabel'):
                fraudLabelId = box.fraudLabel.idLabel

            params = (
                box.xCenter,
                box.yCenter,
                box.width,
                box.height,
                box.xPixel,
                box.yPixel,
                box.widthPixel,
                box.heightPixel,
                fraudTemplateId,
                fraudLabelId
            )

            box_id = self.db_util.execute_query(query, params, commit=True)

            return box_id
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.create: {str(e)}")
            raise

    def update(self, box):
        """
        Cập nhật bounding box

        Args:
            box (BoundingBox): Đối tượng BoundingBox cần cập nhật

        Returns:
            bool: True nếu cập nhật thành công, False nếu không
        """
        try:
            query = """
                UPDATE BoundingBox
                SET xCenter = %s, yCenter = %s, width = %s, height = %s,
                    xPixel = %s, yPixel = %s, widthPixel = %s, heightPixel = %s, 
                    fraudTemplateId = %s, fraudLabelId = %s
                WHERE idBox = %s
            """

            # Lấy ID của FraudTemplate và FraudLabel
            fraudTemplateId = box.fraudTemplateId
            if not fraudTemplateId and box.fraudTemplate and hasattr(box.fraudTemplate, 'idTemplate'):
                fraudTemplateId = box.fraudTemplate.idTemplate

            fraudLabelId = box.fraudLabelId
            if not fraudLabelId and box.fraudLabel and hasattr(box.fraudLabel, 'idLabel'):
                fraudLabelId = box.fraudLabel.idLabel

            params = (
                box.xCenter,
                box.yCenter,
                box.width,
                box.height,
                box.xPixel,
                box.yPixel,
                box.widthPixel,
                box.heightPixel,
                fraudTemplateId,
                fraudLabelId,
                box.idBox
            )

            self.db_util.execute_query(query, params, commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.update: {str(e)}")
            raise

    def delete(self, box_id):
        """
        Xóa bounding box theo ID

        Args:
            box_id (int): ID của bounding box cần xóa

        Returns:
            bool: True nếu xóa thành công, False nếu không
        """
        try:
            query = "DELETE FROM BoundingBox WHERE idBox = %s"
            self.db_util.execute_query(query, (box_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in BoundingBoxDAO.delete: {str(e)}")
            raise

    def delete_by_label_id(self, label_id):
        """
        Xóa tất cả các bounding box theo FraudLabel ID

        Args:
            label_id (int): ID của FraudLabel

        Returns:
            bool: True nếu xóa thành công, False nếu không
        """
        try:
            query = "DELETE FROM BoundingBox WHERE fraudLabelId = %s"
            self.db_util.execute_query(query, (label_id,), commit=True)

            return True
        except Exception as e:
            logging.error(
                f"Error in BoundingBoxDAO.delete_by_label_id: {str(e)}")
            raise

    def delete_by_template_id(self, template_id):
        """
        Xóa tất cả các bounding box theo FraudTemplate ID

        Args:
            template_id (int): ID của FraudTemplate

        Returns:
            bool: True nếu xóa thành công, False nếu không
        """
        try:
            query = "DELETE FROM BoundingBox WHERE fraudTemplateId = %s"
            self.db_util.execute_query(query, (template_id,), commit=True)

            return True
        except Exception as e:
            logging.error(
                f"Error in BoundingBoxDAO.delete_by_template_id: {str(e)}")
            raise

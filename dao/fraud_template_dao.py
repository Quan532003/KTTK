import logging
from utils.db_util import DatabaseUtil
from models.fraud_template import FraudTemplate
from models.fraud_label import FraudLabel
from models.bounding_box import BoundingBox
from datetime import datetime


class FraudTemplateDAO:
    def __init__(self):
        self.db_util = DatabaseUtil()

    def get_all(self):
        """
        Lấy tất cả các mẫu gian lận kèm theo nhãn và bounding box

        Returns:
            list: Danh sách các đối tượng FraudTemplate đã bao gồm labels và boundingBoxes
        """
        try:
            # Lấy tất cả các mẫu gian lận
            query_templates = "SELECT * FROM FraudTemplate"
            template_rows = self.db_util.execute_query(
                query_templates, fetchall=True)

            if not template_rows:
                return []

            # Lấy tất cả các nhãn một lần
            query_all_labels = "SELECT * FROM FraudLabel"
            label_rows = self.db_util.execute_query(
                query_all_labels, fetchall=True)

            # Lấy tất cả các bounding box một lần
            query_all_boxes = "SELECT * FROM BoundingBox"
            box_rows = self.db_util.execute_query(
                query_all_boxes, fetchall=True)

            # Tạo dictionary để dễ dàng tra cứu các nhãn theo ID
            labels_by_id = {label['idLabel']: label for label in label_rows}
            
            # Nhóm các nhãn theo template_id
            labels_by_template = {}
            for label in label_rows:
                template_id = label['fraudTemplateId']
                if template_id not in labels_by_template:
                    labels_by_template[template_id] = []
                labels_by_template[template_id].append(label)
            
            # Nhóm các box theo template_id và label_id
            boxes_by_template = {}
            for box in box_rows:
                template_id = box['fraudTemplateId']
                if template_id not in boxes_by_template:
                    boxes_by_template[template_id] = []
                boxes_by_template[template_id].append(box)

            # Tạo các đối tượng template và thiết lập mối quan hệ
            templates = []
            for template_row in template_rows:
                template_id = template_row['idTemplate']
                
                template = FraudTemplate(
                    idTemplate=template_id,
                    description=template_row['description'],
                    imageUrl=template_row['imageUrl'],
                    timeUpdate=template_row['timeUpdate']
                )
                
                # Khởi tạo danh sách rỗng
                template.labels = []
                template.boundingBoxList = []
                
                # Thêm các nhãn cho template
                template_labels = labels_by_template.get(template_id, [])
                for label_row in template_labels:
                    label = FraudLabel(
                        idLabel=label_row['idLabel'],
                        description=label_row['description'],
                        typeLabel=label_row['typeLabel']
                    )
                    label.boundingBoxList = []
                    template.labels.append(label)
                
                # Tạo dictionary để dễ dàng tra cứu các label theo ID
                template_labels_by_id = {label.idLabel: label for label in template.labels}
                
                # Thêm các bounding box cho template
                template_boxes = boxes_by_template.get(template_id, [])
                for box_row in template_boxes:
                    label_id = box_row['fraudLabelId']
                    label = template_labels_by_id.get(label_id)
                    
                    box = BoundingBox(
                        idBox=box_row['idBox'],
                        xCenter=box_row['xCenter'],
                        yCenter=box_row['yCenter'],
                        width=box_row['width'],
                        height=box_row['height'],
                        xPixel=box_row['xPixel'],
                        yPixel=box_row['yPixel'],
                        widthPixel=box_row['widthPixel'],
                        heightPixel=box_row['heightPixel'],
                        fraudTemplateId=template_id,
                        fraudLabelId=label_id,
                        fraudTemplate=template,
                        fraudLabel=label
                    )
                    
                    template.boundingBoxList.append(box)
                    
                    # Thêm box vào label nếu label tồn tại
                    if label:
                        label.boundingBoxList.append(box)
                
                templates.append(template)
                
            logging.info(f"Retrieved {len(templates)} templates with {sum(len(t.labels) for t in templates)} labels and {sum(len(t.boundingBoxList) for t in templates)} boxes")
            return templates
        except Exception as e:
            logging.error(f"Error in FraudTemplateDAO.get_all: {str(e)}")
            raise

    def get_by_id(self, template_id):
        """
        Lấy mẫu gian lận theo ID kèm theo nhãn và bounding box

        Args:
            template_id (int): ID của mẫu gian lận

        Returns:
            FraudTemplate: Đối tượng FraudTemplate tương ứng đã bao gồm labels và boundingBoxes hoặc None nếu không tìm thấy
        """
        try:
            # Lấy thông tin template
            query_template = "SELECT * FROM FraudTemplate WHERE idTemplate = %s"
            template_row = self.db_util.execute_query(
                query_template, (template_id,), fetchone=True)

            if not template_row:
                return None

            template = FraudTemplate(
                idTemplate=template_row['idTemplate'],
                description=template_row['description'],
                imageUrl=template_row['imageUrl'],
                timeUpdate=template_row['timeUpdate']
            )

            # Khởi tạo danh sách rỗng
            template.labels = []
            template.boundingBoxList = []

            # Lấy tất cả các nhãn của template
            query_labels = "SELECT * FROM FraudLabel WHERE fraudTemplateId = %s"
            label_rows = self.db_util.execute_query(
                query_labels, (template_id,), fetchall=True)

            # Tạo dictionary để dễ dàng tra cứu các label theo ID
            labels_by_id = {}

            # Thiết lập các nhãn
            for label_row in label_rows:
                label = FraudLabel(
                    idLabel=label_row['idLabel'],
                    description=label_row['description'],
                    typeLabel=label_row['typeLabel']
                )
                label.boundingBoxList = []
                template.labels.append(label)
                labels_by_id[label.idLabel] = label

            # Lấy tất cả các bounding box của template
            query_boxes = "SELECT * FROM BoundingBox WHERE fraudTemplateId = %s"
            box_rows = self.db_util.execute_query(
                query_boxes, (template_id,), fetchall=True)

            # Thiết lập các bounding box
            for box_row in box_rows:
                label_id = box_row['fraudLabelId']
                label = labels_by_id.get(label_id)
                
                box = BoundingBox(
                    idBox=box_row['idBox'],
                    xCenter=box_row['xCenter'],
                    yCenter=box_row['yCenter'],
                    width=box_row['width'],
                    height=box_row['height'],
                    xPixel=box_row['xPixel'],
                    yPixel=box_row['yPixel'],
                    widthPixel=box_row['widthPixel'],
                    heightPixel=box_row['heightPixel'],
                    fraudTemplateId=box_row['fraudTemplateId'],
                    fraudLabelId=box_row['fraudLabelId'],
                    fraudTemplate=template,
                    fraudLabel=label
                )
                
                template.boundingBoxList.append(box)
                
                # Thêm box vào label nếu label tồn tại
                if label:
                    label.boundingBoxList.append(box)

            logging.info(f"Retrieved template {template_id} with {len(template.labels)} labels and {len(template.boundingBoxList)} boxes")
            return template
        except Exception as e:
            logging.error(f"Error in FraudTemplateDAO.get_by_id: {str(e)}")
            raise

    def create(self, template):
        """
        Tạo mẫu gian lận mới

        Args:
            template (FraudTemplate): Đối tượng FraudTemplate cần tạo

        Returns:
            int: ID của mẫu gian lận vừa tạo
        """
        try:
            query = """
                INSERT INTO FraudTemplate (description, imageUrl, timeUpdate)
                VALUES (%s, %s, %s)
            """

            time_update = template.timeUpdate
            if isinstance(time_update, datetime):
                time_update = time_update.strftime('%Y-%m-%d %H:%M:%S')

            params = (
                template.description,
                template.imageUrl,
                time_update
            )

            template_id = self.db_util.execute_query(
                query, params, commit=True)

            # Lưu các FraudLabel và BoundingBox
            if template.labels:
                from dao.fraud_label_dao import FraudLabelDAO
                fraud_label_dao = FraudLabelDAO()

                for label in template.labels:
                    label.fraudTemplateId = template_id
                    # Gán đối tượng template để có thể sử dụng trong FraudLabel
                    label.fraudTemplate = template
                    label_id = fraud_label_dao.create(label)

                    # Lưu các BoundingBox nếu có
                    if label.boundingBoxList:
                        from dao.bounding_box_dao import BoundingBoxDAO
                        bounding_box_dao = BoundingBoxDAO()

                        for box in label.boundingBoxList:
                            box.fraudLabelId = label_id
                            box.fraudTemplateId = template_id
                            box.fraudLabel = label
                            box.fraudTemplate = template
                            bounding_box_dao.create(box)

            return template_id
        except Exception as e:
            logging.error(f"Error in FraudTemplateDAO.create: {str(e)}")
            raise

    def update(self, template):
        """
        Cập nhật mẫu gian lận

        Args:
            template (FraudTemplate): Đối tượng FraudTemplate cần cập nhật

        Returns:
            bool: True nếu cập nhật thành công, False nếu không
        """
        try:
            query = """
                UPDATE FraudTemplate
                SET description = %s, imageUrl = %s, timeUpdate = %s
                WHERE idTemplate = %s
            """

            time_update = template.timeUpdate
            if isinstance(time_update, datetime):
                time_update = time_update.strftime('%Y-%m-%d %H:%M:%S')

            params = (
                template.description,
                template.imageUrl,
                time_update,
                template.idTemplate
            )

            self.db_util.execute_query(query, params, commit=True)

            # Xóa tất cả các BoundingBox cũ
            from dao.bounding_box_dao import BoundingBoxDAO
            bounding_box_dao = BoundingBoxDAO()
            bounding_box_dao.delete_by_template_id(template.idTemplate)

            # Xóa tất cả các FraudLabel cũ
            from dao.fraud_label_dao import FraudLabelDAO
            fraud_label_dao = FraudLabelDAO()
            fraud_label_dao.delete_by_template_id(template.idTemplate)

            # Tạo lại các FraudLabel và BoundingBox
            if template.labels:
                for label in template.labels:
                    label.fraudTemplateId = template.idTemplate
                    label.fraudTemplate = template
                    label_id = fraud_label_dao.create(label)

                    if label.boundingBoxList:
                        for box in label.boundingBoxList:
                            box.fraudLabelId = label_id
                            box.fraudTemplateId = template.idTemplate
                            box.fraudLabel = label
                            box.fraudTemplate = template
                            bounding_box_dao.create(box)

            return True
        except Exception as e:
            logging.error(f"Error in FraudTemplateDAO.update: {str(e)}")
            raise

    def delete(self, template_id):
        """
        Xóa mẫu gian lận theo ID

        Args:
            template_id (int): ID của mẫu gian lận cần xóa

        Returns:
            bool: True nếu xóa thành công, False nếu không
        """
        try:
            # BoundingBox và FraudLabel sẽ tự động bị xóa do ràng buộc CASCADE
            query = "DELETE FROM FraudTemplate WHERE idTemplate = %s"
            self.db_util.execute_query(query, (template_id,), commit=True)

            return True
        except Exception as e:
            logging.error(f"Error in FraudTemplateDAO.delete: {str(e)}")
            raise
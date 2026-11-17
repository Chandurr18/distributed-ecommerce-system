
from src.models.notification_model import Notification


class NotificationRepository:
    def __init__(self, db):
        self.db = db

    def create_order_confirmation(
        self,
        user_id,
        order_id,
    ):
        notification = Notification(
            user_id=user_id,
            order_id=order_id,
            notification_type="order_confirmation",
            message="Your order has been received successfully!",
            status="pending",
        )

        self.db.add(notification)

        return notification

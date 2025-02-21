from datetime import datetime, timedelta
import jwt
from flask import current_app
from models.account import ChatUser, db
from services.errors.account import AccountLoginError, AccountNotFoundError, AccountPasswordError
from libs.helper import generate_token

class ChatUserService:
    @classmethod
    def get_jwt_token(cls, chat_user: ChatUser, expire_in: int = 86400) -> str:
        """Generate JWT token for chat user."""
        payload = {
            'type': 'chat_user',
            'user_id': str(chat_user.id),
            'exp': datetime.utcnow() + timedelta(seconds=expire_in)
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    @classmethod
    def authenticate(cls, email: str, password: str) -> ChatUser:
        """Authenticate chat user."""
        chat_user = ChatUser.query.filter_by(email=email).first()
        if not chat_user:
            raise AccountNotFoundError()

        if not chat_user.password:
            raise AccountLoginError()

        if chat_user.password != password:  # 简单密码比较，可以根据需要改为加密比较
            raise AccountPasswordError()

        return chat_user

    @classmethod
    def login(cls, chat_user: ChatUser) -> dict:
        """Login chat user and return token pair."""
        access_token = cls.get_jwt_token(chat_user)
        refresh_token = generate_token()

        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    @classmethod
    def refresh_token(cls, refresh_token: str) -> dict:
        """Refresh access token."""
        try:
            # 这里可以添加 refresh_token 的验证逻辑
            chat_user = ChatUser.query.first()  # 临时实现，应该根据 refresh_token 找到对应用户
            if not chat_user:
                raise AccountNotFoundError()

            access_token = cls.get_jwt_token(chat_user)
            new_refresh_token = generate_token()

            return {
                'access_token': access_token,
                'refresh_token': new_refresh_token
            }
        except Exception as e:
            raise AccountLoginError(str(e))

from flask import request
from flask_restful import Resource, reqparse
from werkzeug.exceptions import Unauthorized

from controllers.console import api
from controllers.console.wraps import setup_required
from libs.helper import extract_remote_ip
from services.chat_user_service import ChatUserService
from services.errors.account import AccountLoginError, AccountNotFoundError, AccountPasswordError

class ChatUserLoginApi(Resource):
    @setup_required
    def post(self):
        """Authenticate chat user and login."""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, location='json')
        parser.add_argument('password', type=str, required=True, location='json')
        args = parser.parse_args()

        try:
            user = ChatUserService.authenticate(args['username'], args['password'])
            token_pair = ChatUserService.login(user, extract_remote_ip(request))
            return {'result': 'success', 'data': token_pair}
        except AccountNotFoundError:
            raise Unauthorized('Invalid username or password')
        except AccountPasswordError:
            raise Unauthorized('Invalid username or password')
        except AccountLoginError as e:
            raise Unauthorized(str(e))

class ChatUserRefreshTokenApi(Resource):
    @setup_required
    def post(self):
        """Refresh access token."""
        parser = reqparse.RequestParser()
        parser.add_argument('refresh_token', type=str, required=True, location='json')
        args = parser.parse_args()

        try:
            new_token_pair = ChatUserService.refresh_token(args['refresh_token'])
            return {'result': 'success', 'data': new_token_pair}
        except Exception as e:
            return {'result': 'fail', 'data': str(e)}, 401

# Register routes
api.add_resource(ChatUserLoginApi, '/chat-user/login')
api.add_resource(ChatUserRefreshTokenApi, '/chat-user/refresh-token')

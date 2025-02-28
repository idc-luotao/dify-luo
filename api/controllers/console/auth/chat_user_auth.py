from flask import request
from flask_restful import Resource, reqparse
from werkzeug.exceptions import Unauthorized

from controllers.console import api

from services.chat_user_service import ChatUserService
from services.errors.account import AccountLoginError, AccountNotFoundError, AccountPasswordError

class ChatUserLoginApi(Resource):

    def post(self):
        """Chat user login with email and password."""
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, location='json')
        parser.add_argument('password', type=str, required=True, location='json')
        args = parser.parse_args()

        try:
            chat_user = ChatUserService.authenticate(args['email'], args['password'])
            token_pair = ChatUserService.login(chat_user)
            return {'result': 'success', 'data': token_pair.model_dump(),'username':chat_user.email}
        except AccountNotFoundError:
            return {'result': 'fail'}
        except AccountPasswordError:
            return {'result': 'fail'}
        except AccountLoginError as e:
            raise Unauthorized(str(e))

class ChatUserRefreshTokenApi(Resource):
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

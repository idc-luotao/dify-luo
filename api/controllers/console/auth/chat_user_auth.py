from flask import request
from flask_restful import Resource, reqparse
from werkzeug.exceptions import Unauthorized

from controllers.console import api
from models.model import ApiToken, App
from services.chat_user_service import ChatUserService
from services.errors.account import AccountLoginError, AccountNotFoundError, AccountPasswordError

class ChatUserLoginApi(Resource):

    def post(self):
        """Chat user login with email and password."""
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, location='json',
                          help='Email is required')
        parser.add_argument('password', type=str, required=True, location='json')
        args = parser.parse_args()

        try:
            chat_user = ChatUserService.authenticate(args['email'], args['password'])
            token_pair = ChatUserService.login(chat_user)
            
            # 根据chatUser的tenantId查询api_tokens表的token
            app = App.query.filter_by(created_by=chat_user.admin_user_id).first()
            api_token = ApiToken.query.filter_by(app_id=app.id).first()
            app_token = api_token.token if api_token else None
            
            return {'result': 'success'
                    , 'data': token_pair.model_dump()
                    ,'username':chat_user.email
                    ,'app_token': app_token
                    }
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

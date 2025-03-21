from flask import request
from flask_restful import Resource, reqparse
from flask_login import current_user
from models.account import ChatUser, db,Account
from werkzeug.exceptions import NotFound, Conflict
from controllers.console import api
from controllers.console.wraps import (
    account_initialization_required,
    setup_required,
)

class ChatUserListApi(Resource):
   
    @setup_required
    @account_initialization_required
    def get(self):
        """获取用户列表"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        users = ChatUser.query.filter(ChatUser.admin_user_id == current_user.id).paginate(page=page, per_page=per_page)
        
        return {
            'data': [{
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'avatar_url': user.avatar_url,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            } for user in users.items],
            'total': users.total,
            'page': users.page,
            'per_page': users.per_page,
            'num_pages': users.pages
        }

    @setup_required
    @account_initialization_required
    def post(self):
        """创建新用户"""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, 
                          help='Username is required')
        parser.add_argument('email', type=str)
        parser.add_argument('password', type=str, required=True,
                          help='Password is required')
        parser.add_argument('avatar_url', type=str)
        args = parser.parse_args()
        
        # 检查用户名是否已存在
        if ChatUser.query.filter_by(username=args['username']).first():
            raise Conflict('Username already exists')

        # 对密码进行哈希处理
        hashed_password = args['password']

        user = ChatUser(
            username=args['username'],
            email=args['email'],
            password=hashed_password,
            avatar_url=args['avatar_url'],
            tenant_id=current_user.current_tenant_id,  # 获取当前用户的tenant_id并指定给新的ChatUser
            admin_user_id=current_user.id  # 设置创建者ID为当前管理员用户的ID
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            return {
                'data': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'avatar_url': user.avatar_url,
                    'tenant_id': str(user.tenant_id) if user.tenant_id else None,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                }
            }, 201
        except Exception:
            db.session.rollback()
            raise

class ChatUserApi(Resource):
    @setup_required
    @account_initialization_required
    def get(self, user_id):
        """获取单个用户"""
        user = ChatUser.query.get(user_id)
        if not user:
            raise NotFound('User not found')
            
        return {
            'data': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'avatar_url': user.avatar_url,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            }
        }

    @setup_required
    @account_initialization_required
    def put(self, user_id):
        """更新用户信息"""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, 
                          help='Username is required')
        parser.add_argument('email', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('avatar_url', type=str)
        args = parser.parse_args()

        user = ChatUser.query.get(user_id)
        if not user:
            raise NotFound('User not found')
        
        # 如果要更改用户名，检查新用户名是否已存在
        if args['username'] != user.username and \
           ChatUser.query.filter_by(username=args['username']).first():
            raise Conflict('Username already exists')

        try:
            user.username = args['username']
            user.email = args['email']
            # 如果提供了新密码，则更新密码
            if args['password']:
                user.password = args['password']
            user.avatar_url = args['avatar_url']
            db.session.commit()
            
            return {
                'data': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'avatar_url': user.avatar_url,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                }
            }
        except Exception:
            db.session.rollback()
            raise

    @setup_required
    @account_initialization_required
    def delete(self, user_id):
        """删除用户"""
        user = ChatUser.query.get(user_id)
        if not user:
            raise NotFound('User not found')

        try:
            db.session.delete(user)
            db.session.commit()
            return '', 204
        except Exception:
            db.session.rollback()
            raise

class GetUserTypeApi(Resource):
    @setup_required
    def get(self):
        """根据用户名判断用户类型"""
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str, required=True, 
                          help='email is required', location='args')
        args = parser.parse_args()

        # 先从 account 表中查询
        account = Account.query.filter_by(email=args['email']).first()
        if account:
            return {
                'data': {
                    'admin_user': 1
                }
            }

        # 从 chat_users 表中查询
        chat_user = ChatUser.query.filter_by(email=args['email']).first()
        if chat_user:
            return {
                'data': {
                    'admin_user': 0
                }
            }

        # 都没有找到
        return {
            'data': {
                'admin_user': None
            }
        }

# 注册路由
api.add_resource(ChatUserListApi, '/chat-users')
api.add_resource(ChatUserApi, '/chat-users/<string:user_id>')
api.add_resource(GetUserTypeApi, '/user/get_type')

import json
import logging
import flask_login  # type: ignore
from flask import Response
from flask_login import user_loaded_from_request, user_logged_in
from werkzeug.exceptions import Unauthorized

import contexts
from dify_app import DifyApp
from libs.passport import PassportService
from services.account_service import AccountService

login_manager = flask_login.LoginManager()


# Flask-Login configuration
# URL whitelist that doesn't require authentication
WHITELIST_URLS = [
    '/console/api/files/upload',  # 健康检查接口
    '/console/api/datasets/init',  # 数据集文档接口
]

@login_manager.request_loader
def load_user_from_request(request_from_flask_login):
    """Load user based on the request."""

    current_path = request_from_flask_login.path
    logging.info(f"check token for url, current_path: {current_path}")
    # if current_path in WHITELIST_URLS:
    #     logging.info(f"URL {current_path} is in whitelist, skip authentication")
    #     logged_in_account = AccountService.load_logged_in_account(account_id="d078a59e-92c1-4a7c-af30-b81887cfed36")
    #     return logged_in_account

    if request_from_flask_login.blueprint not in {"console", "inner_api"}:
        return None
    # Check if the user_id contains a dot, indicating the old format
    auth_header = request_from_flask_login.headers.get("Authorization", "")
    if not auth_header:
        auth_token = request_from_flask_login.args.get("_token")
        if not auth_token:
            raise Unauthorized("Invalid Authorization token.")
    else:
        if " " not in auth_header:
            raise Unauthorized("Invalid Authorization header format. Expected 'Bearer <api-key>' format.")
        auth_scheme, auth_token = auth_header.split(None, 1)
        auth_scheme = auth_scheme.lower()
        if auth_scheme != "bearer":
            raise Unauthorized("Invalid Authorization header format. Expected 'Bearer <api-key>' format.")

    logging.info(f"check token from http header, auth_token: {auth_token}")
    decoded = PassportService().verify(auth_token)
    user_id = decoded.get("user_id")
    logging.info(f"load user info from session, user_id: {user_id}")
    logged_in_account = AccountService.load_logged_in_account(account_id=user_id)
    return logged_in_account


@user_logged_in.connect
@user_loaded_from_request.connect
def on_user_logged_in(_sender, user):
    """Called when a user logged in."""
    if user:
        contexts.tenant_id.set(user.current_tenant_id)


@login_manager.unauthorized_handler
def unauthorized_handler():
    """Handle unauthorized requests."""
    return Response(
        json.dumps({"code": "unauthorized", "message": "Unauthorized."}),
        status=401,
        content_type="application/json",
    )


def init_app(app: DifyApp):
    login_manager.init_app(app)

import time
import datetime
import requests

import click
import logging
import app
from configs import dify_config
from core.rag.datasource.vdb.tidb_on_qdrant.tidb_service import TidbService
from models.dataset import TidbAuthBinding
from extensions.ext_database import db
from models.model import AppMode, AppModelConfig, App


@app.celery.task(queue="dataset")
def update_system_prompt():
    """Update system prompt."""
    click.echo(click.style("Update system prompt.", fg="green"))
    start_at = time.perf_counter()
    try:
        logging.info("this is schedule!!!!")
        click.echo(click.style("Update system prompt.", fg="green"))
        # app_model = (
        #         db.session.query(App)
        #         .filter(App.id == "app_id", App.status == "normal")
        #         .first()
        #     )
        # 查询所有应用
        apps = db.session.query(App).all()
        
        # 如果需要筛选特定模式的应用，例如聊天模式
        # chat_apps = db.session.query(App).filter(App.mode == AppMode.CHAT.value).all()
        
        # 如果需要按ID查询特定应用
        # app = db.session.query(App).filter(App.id == 'your-app-id').first()
        
        # 如果需要查询最近创建的10个应用
        # recent_apps = db.session.query(App).order_by(App.created_at.desc()).limit(10).all()
        
        # 校验apps的长度，如果为空则不处理
        if not apps:
            logging.info("No apps found, skipping system prompt update.")
            return
        
        pre_prompt = getPromptFromRemote()
        if not pre_prompt:
            logging.info("No pre_prompt found, skipping system prompt update.")
            return

        # 取第一个元素
        app = apps[0]
        logging.info(f"Processing app: {app.name}, ID: {app.id},app_model_config_id:{app.app_model_config_id}")
        app_model_config_id = app.app_model_config_id
        
        # 用app_model_config_id作为主键，查询app_model_config表的数据
        app_model_config = db.session.query(AppModelConfig).filter(
            AppModelConfig.id == app_model_config_id
        ).first()
        
        if not app_model_config:
            logging.error(f"App model config not found for ID: {app_model_config_id}")
            return
            
        logging.info(f"Found app model config: {app_model_config.id}")
        
        # 创建新的 AppModelConfig 记录
        new_app_model_config = AppModelConfig(
            app_id=app.id,
            created_by=app_model_config.created_by,
            updated_by=app_model_config.updated_by
        )
        
        # 从现有配置复制所有属性
        model_config_dict = app_model_config.to_dict()
        
        # 更新系统提示词 (pre_prompt)
        model_config_dict["pre_prompt"] = pre_prompt
        
        # 使用更新后的配置字典更新新的 AppModelConfig
        new_app_model_config = new_app_model_config.from_model_config_dict(model_config_dict)
        
        # 保存新的 AppModelConfig
        db.session.add(new_app_model_config)
        db.session.flush()
        
        # 更新 App 的 app_model_config_id 指向新创建的记录
        app.app_model_config_id = new_app_model_config.id
        
        # 设置app的更新时间
        app.updated_at = datetime.datetime.now()
        
        # 提交事务
        db.session.commit()
        
        logging.info(f"Updated system prompt for app: {app.name}, new config ID: {new_app_model_config.id}")
        
        # # check the number of idle tidb serverless
        # tidb_serverless_list = TidbAuthBinding.query.filter(
        #     TidbAuthBinding.active == False, TidbAuthBinding.status == "CREATING"
        # ).all()
        # if len(tidb_serverless_list) == 0:
        #     return
        # # update tidb serverless status
        # update_clusters(tidb_serverless_list)

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))

    end_at = time.perf_counter()
    click.echo(
        click.style("Update tidb serverless status task success latency: {}".format(end_at - start_at), fg="green")
    )


def getPromptFromRemote():
    # 从环境变量配置中获取PROMPT_API_URL
    url = dify_config.PROMPT_API_URL
    
    try:
        # 发送 GET 请求
        response = requests.get(url)
        
        # 检查HTTP响应状态码
        response.raise_for_status()  # 如果状态码不是200，会抛出异常
        
        # 解析JSON响应
        json_response = response.json()
        print('Response Body:', json_response)
        
        # 检查是否包含message属性
        if 'message' in json_response:
            message = json_response['message']
            print('Message:', message)
            
            # 返回获取到的message
            return message
        else:
            print('Response does not contain a message attribute')
            return None
    
    except requests.exceptions.RequestException as e:
        # 处理请求异常
        print(f"Error making request: {e}")
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return None
    
    except ValueError as e:
        # 处理JSON解析异常
        print(f"Error parsing JSON response: {e}")
        return None

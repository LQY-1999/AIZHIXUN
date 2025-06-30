from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests
from flask import send_from_directory
from sqlalchemy import text
from datetime import datetime
import time
import random
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from flask import session
import secrets
from functools import wraps
from sqlalchemy import func
import csv
from io import StringIO

app = Flask(__name__, template_folder='templates')
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.abspath(DB_PATH)}'  # 已废弃，直接用agent_config.db
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)  # 允许跨域请求

print('数据库绝对路径:', os.path.abspath('agent_config.db'))
# 修改数据库URI为绝对路径
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.abspath('agent_config.db')
db = SQLAlchemy(app)

# 更新Dify API配置
DIFY_API_URL = "http://8.148.26.204:41/v1/chat-messages"
DIFY_API_KEY = "app-UC0l1p6JW9r5cFG3TZIJi6t0"

# 新增WhaleDI API配置
WHALEDI_API_URL = "http://10.10.186.14:31001/knowledge/knowledgeService/api/v1/chat/completions"
WHALEDI_API_KEY = "WhaleDI-Agent-7fc20b57f24c62fe70153616382dfbf87d38baf52dcd632fd50d4f48b871af61"

# 数据模型
class ConversationHistory(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    config = db.Column(db.JSON)
    messages = db.Column(db.JSON)
    status = db.Column(db.String(20))  # 'active' or 'ended'
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    end_time = db.Column(db.DateTime)
    api_type = db.Column(db.String(20), default='dify')  # 'dify' or 'whaledi'

class Lianxifangshi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Yewuchangjing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Monijuese(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Xunlianjuese(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Yingxiaodafa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Shilihuashu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class ApiConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    key = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # dify/whaledi

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    userid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    is_active = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 数据库初始化
def init_db():
    """初始化数据库和表"""
    try:
        # 创建所有表
        db.create_all()
        
        # 检查是否需要初始化数据
        if Lianxifangshi.query.first() is None:
            # 添加默认数据
            items = ['一对一练习', '团队练习', '自主练习']
            for item in items:
                db.session.add(Lianxifangshi(name=item))
            
            items = ['终端销售', '线上咨询', '电话营销']
            for item in items:
                db.session.add(Yewuchangjing(name=item))
                
            items = ['门店店员', '直销人员', '客服代表']
            for item in items:
                db.session.add(Monijuese(name=item))
                
            items = ['销售新人', '资深销售', '销售主管']
            for item in items:
                db.session.add(Xunlianjuese(name=item))
                
            items = ['产品介绍', '需求挖掘', '异议处理', '成交促进']
            for item in items:
                db.session.add(Yingxiaodafa(name=item))
                
            items = ['您好，请问有什么可以帮您?', '这个产品的优势是...', '我理解您的顾虑...']
            for item in items:
                db.session.add(Shilihuashu(name=item))
            
            db.session.commit()
            print("数据库初始化完成")
    except Exception as e:
        db.session.rollback()
        print(f"数据库初始化失败: {str(e)}")
        raise

# 添加一个全局集合来存储已结束的会话ID
ended_conversations = set()

def get_api_config_by_type(api_type):
    config = ApiConfig.query.filter_by(type=api_type).first()
    if not config:
        raise Exception(f"未找到{api_type}的API配置，请在后台添加")
    return config

def call_dify_api(data):
    """调用Dify API并处理响应"""
    config = get_api_config_by_type('dify')
    headers = {
        'Authorization': f'Bearer {config.key}',
        'Content-Type': 'application/json'
    }
    request_data = {
        'inputs': {
            'lianxifangshi': data.get('lianxifangshi'),
            'yewuchangjing': data.get('yewuchangjing'),
            'monijuese': data.get('monijuese'),
            'xunlianjuese': data.get('xunlianjuese', ''),
            'yingxiaodafa': data.get('yingxiaodafa', ''),
            'shilihuashu': data.get('shilihuashu', '')
        },
        'query': data.get('query', ''),
        'response_mode': 'blocking',
        'user': 'web_user',
        'conversation_id': data.get('conversation_id', ''),
        'files': data.get('files', [])
    }
    print(f"调用Dify API, 参数: {json.dumps(request_data, ensure_ascii=False)}")
    try:
        response = requests.post(
            config.url,
            headers=headers,
            json=request_data,
            timeout=120
        )
        print(f"API响应: {response.status_code}, 内容: {response.text}")
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('answer', '')
            if ai_response:
                try:
                    import re
                    conversation_id_match = re.search(r'"conversation_id"\s*:\s*([^"\s\n]+)', ai_response)
                    if conversation_id_match:
                        end_conversation_id = conversation_id_match.group(1).strip('{}"\' \n\t')
                        return {
                            'ai_response': ai_response,
                            'conversation_id': result.get('conversation_id'),
                            'metadata': {'conversation_id': end_conversation_id}
                        }
                except Exception as e:
                    print(f"解析会话ID失败: {str(e)}")
            return {
                'ai_response': ai_response,
                'conversation_id': result.get('conversation_id'),
                'metadata': result.get('metadata', {})
            }
        else:
            error_msg = f"API调用失败: {response.status_code}"
            if response.text:
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg = error_data['message']
                except:
                    pass
            return {'error': error_msg}, response.status_code
    except requests.exceptions.RequestException as e:
        print(f"API请求异常: {str(e)}")
        return {'error': f"API请求异常: {str(e)}"}, 500

def call_whaledi_api(data):
    """调用WhaleDI API并处理响应"""
    config = get_api_config_by_type('whaledi')
    headers = {
        'Authorization': f'Bearer {config.key}',
        'Content-Type': 'application/json'
    }
    agentlink_data = {
        'lianxifangshi': data.get('lianxifangshi'),
        'yewuchangjing': data.get('yewuchangjing'),
        'monijuese': data.get('monijuese'),
        'xunlianjuese': data.get('xunlianjuese', ''),
        'yingxiaodafa': data.get('yingxiaodafa', ''),
        'shilihuashu': data.get('shilihuashu', '')
    }
    request_data = {
        'chatId': data.get('conversation_id', str(int(time.time()))),
        'stream': False,
        'agentlink': json.dumps(agentlink_data, ensure_ascii=False),
        'messages': [
            {
                'role': 'user',
                'content': data.get('query', '')
            }
        ]
    }
    print(f"调用WhaleDI API, 参数: {json.dumps(request_data, ensure_ascii=False)}")
    try:
        response = requests.post(
            config.url,
            headers=headers,
            json=request_data,
            timeout=120
        )
        print(f"WhaleDI API响应: {response.status_code}, 内容: {response.text}")
        if response.status_code == 200:
            result = response.json()
            ai_response = ''
            if 'choices' in result and len(result['choices']) > 0:
                ai_response = result['choices'][0].get('message', {}).get('content', '')
            elif 'answer' in result:
                ai_response = result['answer']
            elif 'message' in result:
                ai_response = result['message']
            else:
                ai_response = str(result)
            return {
                'ai_response': ai_response,
                'conversation_id': request_data['chatId'],
                'metadata': result.get('metadata', {})
            }
        else:
            error_msg = f"WhaleDI API调用失败: {response.status_code}"
            if response.text:
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg = error_data['message']
                    elif 'error' in error_data:
                        error_msg = error_data['error']
                except:
                    pass
            return {'error': error_msg}, response.status_code
    except requests.exceptions.RequestException as e:
        print(f"WhaleDI API请求异常: {str(e)}")
        return {'error': f"WhaleDI API请求异常: {str(e)}"}, 500

def call_api(data, api_type='dify'):
    """统一的API调用函数，根据api_type选择不同的API"""
    if api_type == 'whaledi':
        return call_whaledi_api(data)
    else:
        return call_dify_api(data)

# ========== 权限校验装饰器提前 ========== 
user_tokens = {}  # userid: token

def verify_token(token):
    # 简单token校验，返回userid
    for userid, t in user_tokens.items():
        if t == token:
            return userid
    return None

def require_token(admin_only=False):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': '未提供token'}), 401
            if token.startswith('Bearer '):
                token = token[7:]
            userid = request.headers.get('Userid')
            if not userid:
                return jsonify({'error': '未提供Userid'}), 401
            user = User.query.filter_by(userid=userid).first()
            if not user:
                return jsonify({'error': '无效的用户'}), 401
            if admin_only and not user.is_admin:
                return jsonify({'error': '无权限'}), 403
            request.current_user = user  # 修复关键：设置当前用户
            return f(*args, **kwargs)
        return wrapper
    return decorator
# ========== 权限校验装饰器提前 ========== 

@app.route('/api/start-session', methods=['POST'])
@require_token()
def start_session():
    try:
        data = request.json
        user = request.current_user
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
        # 如果是健康检查请求
        if data.get('initialize_only'):
            return jsonify({'status': 'ok'})
        # 参数白名单校验
        ALLOWED_PARAMS = ['lianxifangshi', 'yewuchangjing', 'monijuese', 
                         'xunlianjuese', 'yingxiaodafa', 'shilihuashu', 
                         'query', 'api_type']
        # 提取输入参数
        inputs = {
            k: v for k, v in data.items() 
            if k in ALLOWED_PARAMS and k not in ['query', 'api_type']
        }
        # 获取API类型，默认为dify
        api_type = data.get('api_type', 'dify')
        # 必填参数校验
        required_params = ['lianxifangshi', 'yewuchangjing', 'monijuese']
        missing_params = [param for param in required_params if not inputs.get(param)]
        if missing_params:
            return jsonify({'error': f'缺少必要参数: {", ".join(missing_params)}'}), 400
        # 如果是初始化请求，只返回成功状态
        if data.get('initialize_only'):
            return jsonify({'status': 'ok'})
        # 调用API开始新会话，user字段用userid
        result = call_api({
            **inputs,
            'query': data.get('query', ''),
            'user': user.userid
        }, api_type)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        # 保存会话历史
        current_time = datetime.utcnow().isoformat()
        # 合并用户信息到config
        config_with_user = dict(inputs)
        config_with_user['userid'] = user.userid
        config_with_user['username'] = user.username
        conversation = ConversationHistory(
            id=result.get('conversation_id'),
            config=config_with_user,
            messages=[{
                'sender': '用户',
                'text': data.get('query', ''),
                'type': 'user',
                'timestamp': current_time
            }, {
                'sender': 'AI',
                'text': result.get('answer') or result.get('ai_response'),
                'type': 'agent',
                'timestamp': current_time
            }],
            status='active',
            api_type=api_type
        )
        db.session.add(conversation)
        db.session.commit()
        # 返回结果前检查是否有错误
        if result.get('error'):
            return jsonify({'error': result['error']}), 500
        # 确保返回正确的响应格式
        response_data = {
            'answer': result.get('answer') or result.get('ai_response'),
            'conversation_id': result.get('conversation_id'),
            'metadata': result.get('metadata', {})
        }
        return jsonify(response_data)
    except Exception as e:
        print(f"开始会话异常: {str(e)}")
        return jsonify({
            'error': '服务器内部错误',
            'details': str(e)
        }), 500

@app.route('/api/conversation', methods=['POST'])
@require_token()
def conversation():
    try:
        data = request.json
        user = request.current_user
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
        # 验证conversation_id
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return jsonify({'error': '缺少会话ID'}), 400
        # 检查会话是否存在
        conversation = ConversationHistory.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': '会话不存在'}), 404
        # 检查会话是否已结束
        if conversation.status == 'ended':
            return jsonify({
                'error': '会话已结束',
                'ended': True,
                'conversation_id': conversation_id
            }), 403
        # 验证query
        if not data.get('query'):
            return jsonify({'error': '缺少用户输入'}), 400
        # 调用API继续会话，user字段用userid
        result = call_api({
            'query': data.get('query'),
            'conversation_id': conversation_id,
            'user': user.userid,
            **conversation.config
        }, conversation.api_type)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        # 更新会话历史
        current_time = datetime.utcnow().isoformat()
        conversation.messages.extend([{
            'sender': '用户',
            'text': data.get('query'),
            'type': 'user',
            'timestamp': current_time
        }, {
            'sender': 'AI',
            'text': result.get('answer') or result.get('ai_response'),
            'type': 'agent',
            'timestamp': current_time
        }])
        # 确保config里有userid和username
        if 'userid' not in conversation.config:
            conversation.config['userid'] = user.userid
        if 'username' not in conversation.config:
            conversation.config['username'] = user.username
        # 检查是否需要结束会话
        if result.get('metadata', {}).get('conversation_id') == conversation_id:
            conversation.status = 'ended'
            conversation.end_time = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'error': '会话已结束',
                'ended': True,
                'conversation_id': conversation_id
            }), 403
        db.session.commit()
        return jsonify(result)
    except Exception as e:
        print(f"继续会话异常: {str(e)}")
        return jsonify({
            'error': '服务器内部错误',
            'details': str(e)
        }), 500

@app.route('/api/end-session', methods=['POST'])
def end_session():
    """结束特定会话 - 支持Dify的conversation_id和WhaleDI的chatId"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '缺少请求数据'}), 400
            
        # 支持两种参数：conversation_id (Dify) 和 chatId (WhaleDI)
        conversation_id = data.get('conversation_id')
        chat_id = data.get('chatId')
        
        if not conversation_id and not chat_id:
            return jsonify({'error': '缺少会话ID参数，请提供conversation_id或chatId'}), 400
        
        # 确定要结束的会话ID和API类型
        session_id = conversation_id or chat_id
        api_type = 'whaledi' if chat_id else 'dify'
        
        # 检查会话是否存在（优先通过conversation_id查找）
        conversation = None
        if conversation_id:
            conversation = ConversationHistory.query.get(conversation_id)
        elif chat_id:
            # 通过chatId查找对应的会话记录
            conversations = ConversationHistory.query.filter_by(api_type='whaledi').all()
            for conv in conversations:
                if conv.id == chat_id:
                    conversation = conv
                    break
        
        # 如果找到了会话记录，更新其状态
        if conversation:
            conversation.status = 'ended'
            conversation.end_time = datetime.utcnow()
            db.session.commit()
            print(f"已更新本地会话状态: {session_id}")
        
        # 根据API类型调用不同的结束接口
        if api_type == 'dify':
            # 调用Dify API结束会话
            headers = {
                'Authorization': f'Bearer {DIFY_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            end_session_url = f"http://8.148.26.204:41/v1/conversations/{session_id}/end"
            
            try:
                response = requests.post(
                    end_session_url,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return jsonify({
                        'status': 'ok',
                        'message': f'Dify会话 {session_id} 已结束',
                        'conversation_id': session_id,
                        'api_type': 'dify'
                    })
                else:
                    return jsonify({
                        'status': 'ok',
                        'message': f'Dify会话 {session_id} 已在本地结束',
                        'conversation_id': session_id,
                        'api_type': 'dify'
                    })
                    
            except requests.exceptions.RequestException as e:
                return jsonify({
                    'status': 'ok',
                    'message': f'Dify会话 {session_id} 已在本地结束',
                    'conversation_id': session_id,
                    'api_type': 'dify',
                    'note': f'API调用失败: {str(e)}'
                })
        
        elif api_type == 'whaledi':
            # 调用WhaleDI API结束会话
            try:
                config = get_api_config_by_type('whaledi')
                headers = {
                    'Authorization': f'Bearer {config.key}',
                    'Content-Type': 'application/json'
                }
                
                # WhaleDI的结束会话请求（根据实际API调整）
                end_session_data = {
                    'chatId': session_id,
                    'action': 'end'  # 假设WhaleDI有结束会话的action参数
                }
                
                # 如果WhaleDI没有专门的结束接口，可以发送一个特殊的结束消息
                # 或者直接返回成功（因为WhaleDI可能是无状态的）
                response = requests.post(
                    config.url.replace('/chat/completions', '/chat/end'),  # 假设的结束接口
                    headers=headers,
                    json=end_session_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return jsonify({
                        'status': 'ok',
                        'message': f'WhaleDI会话 {session_id} 已结束',
                        'chatId': session_id,
                        'api_type': 'whaledi'
                    })
                else:
                    # 如果WhaleDI没有专门的结束接口，直接返回成功
                    return jsonify({
                        'status': 'ok',
                        'message': f'WhaleDI会话 {session_id} 已标记为结束',
                        'chatId': session_id,
                        'api_type': 'whaledi',
                        'note': 'WhaleDI可能不需要显式结束会话'
                    })
                    
            except Exception as e:
                # 即使API调用失败，也返回成功（因为WhaleDI可能是无状态的）
                return jsonify({
                    'status': 'ok',
                    'message': f'WhaleDI会话 {session_id} 已标记为结束',
                    'chatId': session_id,
                    'api_type': 'whaledi',
                    'note': f'API调用异常: {str(e)}'
                })
        
        else:
            return jsonify({
                'error': '不支持的API类型',
                'api_type': api_type
            }), 400
            
    except Exception as e:
        print(f"结束会话异常: {str(e)}")
        return jsonify({
            'error': '服务器内部错误',
            'details': str(e)
        }), 500

@app.route('/api/config', methods=['GET'])
@require_token()
def get_config():
    """获取配置选项"""
    try:
        # 确保数据库已初始化
        if Lianxifangshi.query.first() is None:
            init_db()
            
        config = {
            'lianxifangshi': [{'value': item.name, 'label': item.name} for item in Lianxifangshi.query.all()],
            'yewuchangjing': [{'value': item.name, 'label': item.name} for item in Yewuchangjing.query.all()],
            'monijuese': [{'value': item.name, 'label': item.name} for item in Monijuese.query.all()],
            'xunlianjuese': [{'value': item.name, 'label': item.name} for item in Xunlianjuese.query.all()],
            'yingxiaodafa': [{'value': item.name, 'label': item.name} for item in Yingxiaodafa.query.all()],
            'shilihuashu': [{'value': item.name, 'label': item.name} for item in Shilihuashu.query.all()],
            'api_types': [
                {'value': 'dify', 'label': 'Dify API'},
                {'value': 'whaledi', 'label': 'WhaleDI API'}
            ]
        }
        
        # 检查是否有空数据
        empty_configs = [k for k, v in config.items() if not v]
        if empty_configs:
            print(f"警告: 以下配置项为空: {', '.join(empty_configs)}")
            
        print(f"API返回的配置数据: {json.dumps(config, ensure_ascii=False)}")
        return jsonify(config)
    except Exception as e:
        print(f"获取配置异常: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/test-agent')
def serve_test_agent():
    return send_from_directory('templates', 'test-agent.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory('templates', 'admin.html')

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/api/check-status')
def check_status():
    """检查服务状态"""
    try:
        # 检查数据库连接
        db.session.execute(text('SELECT 1'))
        
        # 检查Dify API连接
        headers = {
            'Authorization': f'Bearer {DIFY_API_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.get("http://8.148.26.204:41/v1/parameters", headers=headers, timeout=5)
        
        if response.status_code == 200:
            print("Dify API 连接成功")
            return jsonify({'status': 'online'})
            
        print(f"Dify API 连接失败: {response.status_code}")
        return jsonify({'status': 'offline'})
    except Exception as e:
        print(f"状态检查失败: {str(e)}")
        return jsonify({'status': 'offline'})

# 管理后台API路由
@app.route('/api/admin/<string:type>', methods=['GET'])
def get_items(type):
    """获取指定类型的所有配置项"""
    try:
        model = globals().get(type.capitalize())
        if not model:
            return jsonify({'error': '无效的配置类型'}), 400
            
        items = model.query.all()
        return jsonify([{'id': item.id, 'name': item.name} for item in items])
    except Exception as e:
        print(f"获取{type}配置失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/<string:type>', methods=['POST'])
def add_item(type):
    """添加新的配置项"""
    try:
        data = request.json
        if not data or not data.get('name'):
            return jsonify({'error': '缺少必要参数'}), 400
            
        model = globals().get(type.capitalize())
        if not model:
            return jsonify({'error': '无效的配置类型'}), 400
            
        item = model(name=data['name'])
        db.session.add(item)
        db.session.commit()
        
        return jsonify({'id': item.id, 'name': item.name})
    except Exception as e:
        db.session.rollback()
        print(f"添加{type}配置失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/<string:type>/<int:id>', methods=['DELETE'])
def delete_item(type, id):
    """删除指定配置项"""
    try:
        model = globals().get(type.capitalize())
        if not model:
            return jsonify({'error': '无效的配置类型'}), 400
            
        item = model.query.get(id)
        if not item:
            return jsonify({'error': '配置项不存在'}), 404
            
        db.session.delete(item)
        db.session.commit()
        
        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        print(f"删除{type}配置失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/api-config', methods=['GET'])
def get_api_config():
    """获取API配置信息"""
    try:
        config = {
            'dify': {
                'url': DIFY_API_URL,
                'key': DIFY_API_KEY[:20] + '...' if len(DIFY_API_KEY) > 20 else DIFY_API_KEY,
                'name': 'Dify API'
            },
            'whaledi': {
                'url': WHALEDI_API_URL,
                'key': WHALEDI_API_KEY[:20] + '...' if len(WHALEDI_API_KEY) > 20 else WHALEDI_API_KEY,
                'name': 'WhaleDI API'
            }
        }
        return jsonify(config)
    except Exception as e:
        print(f"获取API配置异常: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/api-config', methods=['GET'])
def get_api_configs():
    configs = ApiConfig.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'url': c.url,
        'key': c.key,
        'type': c.type
    } for c in configs])

@app.route('/api/admin/api-config', methods=['POST'])
def add_api_config():
    data = request.json
    config = ApiConfig(
        name=data['name'],
        url=data['url'],
        key=data['key'],
        type=data['type']
    )
    db.session.add(config)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/api-config/<int:id>', methods=['PUT'])
def update_api_config(id):
    data = request.json
    config = ApiConfig.query.get(id)
    if not config:
        return jsonify({'error': '未找到配置'}), 404
    config.name = data['name']
    config.url = data['url']
    config.key = data['key']
    config.type = data['type']
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/api-config/<int:id>', methods=['DELETE'])
def delete_api_config(id):
    config = ApiConfig.query.get(id)
    if not config:
        return jsonify({'error': '未找到配置'}), 404
    db.session.delete(config)
    db.session.commit()
    return jsonify({'success': True})

def generate_token():
    return secrets.token_hex(32)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400
    user = User(username=username)
    user.set_password(password)
    user.is_active = False  # 需管理员激活
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'msg': '注册成功，等待管理员审核激活'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    if not user.is_active:
        return jsonify({'error': '账号未激活，请联系管理员'}), 403
    token = generate_token()
    user_tokens[user.userid] = token
    return jsonify({'success': True, 'token': token, 'userid': user.userid, 'username': user.username, 'is_admin': user.is_admin})

@app.route('/api/users', methods=['GET'])
@require_token(admin_only=True)
def list_users():
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'userid': u.userid,
        'is_active': u.is_active,
        'is_admin': u.is_admin
    } for u in users])

@app.route('/api/users/<int:id>/activate', methods=['POST'])
@require_token(admin_only=True)
def activate_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    user.is_active = True
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:id>/deactivate', methods=['POST'])
@require_token(admin_only=True)
def deactivate_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    user.is_active = False
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:id>', methods=['DELETE'])
@require_token(admin_only=True)
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/users/<int:id>/reset-password', methods=['POST'])
@require_token(admin_only=True)
def reset_user_password(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    user.set_password('123456')  # 重置为默认密码
    db.session.commit()
    return jsonify({'success': True, 'message': '密码已重置为：123456'})

@app.route('/api/users/<int:id>/set-role', methods=['POST'])
@require_token(admin_only=True)
def set_user_role(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    data = request.json
    is_admin = data.get('is_admin', False)
    user.is_admin = is_admin
    db.session.commit()
    return jsonify({'success': True, 'message': f'用户角色已设置为{"管理员" if is_admin else "普通用户"}'})

@app.route('/api/admin/conversation-stats', methods=['GET'])
@require_token(admin_only=True)
def conversation_stats():
    # 总对话数
    total = ConversationHistory.query.count()
    # 活跃用户数（按config中的userid去重）
    active_users = db.session.query(func.count(func.distinct(ConversationHistory.config['userid']))).scalar()
    # API类型分布
    api_type_counts = db.session.query(ConversationHistory.api_type, func.count()).group_by(ConversationHistory.api_type).all()
    api_type_stats = {k: v for k, v in api_type_counts}
    # 按天趋势（近30天）
    days = db.session.query(
        func.strftime('%Y-%m-%d', ConversationHistory.timestamp),
        func.count()
    ).group_by(func.strftime('%Y-%m-%d', ConversationHistory.timestamp)).order_by(func.strftime('%Y-%m-%d', ConversationHistory.timestamp)).all()
    trend = [{'date': d, 'count': c} for d, c in days]
    return {
        'total': total,
        'active_users': active_users,
        'api_type_stats': api_type_stats,
        'trend': trend
    }

@app.route('/api/admin/conversation-logs', methods=['GET'])
@require_token(admin_only=True)
def conversation_logs():
    try:
        # 分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        # 筛选参数
        userid = request.args.get('userid')
        api_type = request.args.get('api_type')
        start = request.args.get('start')
        end = request.args.get('end')
        q = ConversationHistory.query
        if userid:
            q = q.filter(func.json_extract(ConversationHistory.config, '$.userid') == userid)
        if api_type:
            q = q.filter(ConversationHistory.api_type == api_type)
        if start:
            q = q.filter(ConversationHistory.timestamp >= start)
        if end:
            q = q.filter(ConversationHistory.timestamp <= end)
        total = q.count()
        logs = q.order_by(ConversationHistory.timestamp.desc()).offset((page-1)*page_size).limit(page_size).all()
        result = []
        for log in logs:
            try:
                result.append({
                    'id': log.id,
                    'userid': log.config.get('userid') if log.config else '',
                    'username': log.config.get('username') if log.config else '',
                    'api_type': log.api_type,
                    'status': log.status,
                    'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
                    'end_time': log.end_time.strftime('%Y-%m-%d %H:%M:%S') if log.end_time else '',
                    'question': log.messages[0]['text'] if log.messages and len(log.messages) > 0 else '',
                    'answer': log.messages[-1]['text'] if log.messages and len(log.messages) > 1 else '',
                    'messages': log.messages or []
                })
            except Exception as e:
                print(f"处理对话记录 {log.id} 时出错: {e}")
                continue
        return jsonify({'total': total, 'logs': result})
    except Exception as e:
        print(f"对话日志接口异常: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/conversation-logs/export', methods=['GET'])
@require_token(admin_only=True)
def export_conversation_logs():
    # 筛选参数同上
    userid = request.args.get('userid')
    api_type = request.args.get('api_type')
    start = request.args.get('start')
    end = request.args.get('end')
    q = ConversationHistory.query
    if userid:
        q = q.filter(func.json_extract(ConversationHistory.config, '$.userid') == userid)
    if api_type:
        q = q.filter(ConversationHistory.api_type == api_type)
    if start:
        q = q.filter(ConversationHistory.timestamp >= start)
    if end:
        q = q.filter(ConversationHistory.timestamp <= end)
    logs = q.order_by(ConversationHistory.timestamp.desc()).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', '用户ID', '用户名', 'API类型', '状态', '开始时间', '结束时间', '问题', '答案'])
    for log in logs:
        cw.writerow([
            log.id,
            log.config.get('userid') if log.config else '',
            log.config.get('username') if log.config else '',
            log.api_type,
            log.status,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
            log.end_time.strftime('%Y-%m-%d %H:%M:%S') if log.end_time else '',
            log.messages[0]['text'] if log.messages and len(log.messages) > 0 else '',
            log.messages[-1]['text'] if log.messages and len(log.messages) > 1 else '',
        ])
    output = si.getvalue()
    return (output, 200, {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': 'attachment; filename=conversation_logs.csv'
    })

@app.route('/login.html')
def serve_login():
    return send_from_directory('templates', 'login.html')

@app.route('/test-frontend')
def serve_test_frontend():
    return send_from_directory('.', 'test_frontend.html')

@app.route('/api/admin/user-conversation-stats', methods=['GET'])
@require_token(admin_only=True)
def user_conversation_stats():
    try:
        conversations = ConversationHistory.query.all()
        user_stats = {}
        for conv in conversations:
            if conv.config and 'userid' in conv.config:
                userid = conv.config['userid']
                username = conv.config.get('username', '')
                if userid not in user_stats:
                    user_stats[userid] = {
                        'userid': userid,
                        'username': username,
                        'count': 0
                    }
                user_stats[userid]['count'] += 1
        result = list(user_stats.values())
        return jsonify(result)
    except Exception as e:
        print(f"用户对话统计接口异常: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/conversations', methods=['GET'])
@require_token(admin_only=True)
def get_conversations():
    """获取所有对话记录"""
    try:
        conversations = ConversationHistory.query.order_by(ConversationHistory.timestamp.desc()).all()
        result = []
        for conv in conversations:
            try:
                result.append({
                    'id': conv.id,
                    'config': conv.config or {},
                    'messages': conv.messages or [],
                    'status': conv.status,
                    'timestamp': conv.timestamp.isoformat() if conv.timestamp else None,
                    'end_time': conv.end_time.isoformat() if conv.end_time else None,
                    'api_type': conv.api_type
                })
            except Exception as e:
                print(f"处理对话记录 {conv.id} 时出错: {e}")
                continue
        return jsonify(result)
    except Exception as e:
        print(f"获取对话记录异常: {e}")
        return jsonify({'error': str(e)}), 500

# 在应用启动时初始化数据库
with app.app_context():
    try:
        init_db()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_active=True, is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    except Exception as e:
        print(f"应用启动时初始化数据库失败: {str(e)}")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)


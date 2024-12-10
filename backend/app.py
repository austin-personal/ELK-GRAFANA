from flask import Flask, request, jsonify, render_template
import boto3
import os
from flask_cors import CORS
import time
import logging # 로그 수집 라이브러리
from logging.handlers import RotatingFileHandler

# APM 관련 import
from elasticapm.contrib.flask import ElasticAPM

app = Flask(__name__)
CORS(app)

# 로그 디렉토리 확인 및 생성
log_dir = '/app/logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Flask 로거 설정
file_handler = RotatingFileHandler(os.path.join(log_dir, 'app.log'), maxBytes=100000, backupCount=10)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# 기존의 기본 핸들러 제거 (중복 로그 방지)
if app.logger.hasHandlers():
    app.logger.handlers.clear()
    app.logger.addHandler(file_handler)


# APM 설정 (환경변수를 사용하거나 하드코딩 가능)
app.config['ELASTIC_APM'] = {
    'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'my-flask-app'),
    'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://apm-server:8200'),
    'ENVIRONMENT': os.getenv('FLASK_ENV', 'production')
}

apm = ElasticAPM(app)  # APM 인스턴스 초기화

# DynamoDB 클라이언트 생성
dynamodb = boto3.resource('dynamodb',
    region_name='us-east-1', 
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))

table_name = 'buyme-pipelinetest-db'
table = dynamodb.Table(table_name)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/buy', methods=['POST'])
def buy():
    data = request.get_json()
    data['OID'] = int(time.time())
    response = table.put_item(Item=data)

    # 로그 수집
    app.logger.info("Received /buy request")

    return jsonify({"status": "ok", "data": data}), 200

@app.route('/test-log')
def test_log():
    app.logger.info("Test log entry")
    return "Test log entry created", 200

if __name__ == '__main__':
    # 로컬 테스트 시, app.run() 사용
    # 도커 환경에서는 Dockerfile/CMD로 실행
    app.run(host='0.0.0.0', port=4999)

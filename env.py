from os import getenv
from dotenv import load_dotenv
'''
환경 변수 로드 함수
'''
def load_env_vars(env_path, required_vars):
    config = {}
    #환경 변수 파일 로드
    try:
        load_dotenv(env_path)
    except Exception as e:
        raise FileNotFoundError(f"[Fatal] {env_path} is missing. Please create a .env file with the required environment variables.")
    #필수 환경 변수 확인
    for var in required_vars:
        value = getenv(var)
        if value is None:
            raise EnvironmentError(f"[Fatal] Required {var} not found in {env_path}. Please check your environment variables.")
        config[var] = value
    #환경 변수 로드 성공 메시지
    print(f"[Info] Loaded environment variables from {env_path}")
    return config
'''
환경 변수 파일 경로
필수 환경 변수 키 목록
'''
ENV_PATH = '.env'
REQUIRED_KEYS = [
    "NOTION_TOKEN",
    "NOTION_DOCKER_DB_ID",
    "NOTION_JENKINS_DB_ID",
    "NOTION_GAMES_DB_ID",
    "NOTION_DEFAULT_DB_NAME"
]
'''
환경 변수 로드 및 키 설정
'''
_config = load_env_vars(ENV_PATH, REQUIRED_KEYS)
KEYS = {
    "NOTION_TOKEN": _config["NOTION_TOKEN"],
}
DB = {
    "Docker": _config["NOTION_DOCKER_DB_ID"],
    "Jenkins": _config["NOTION_JENKINS_DB_ID"],
    "Games": _config["NOTION_GAMES_DB_ID"]
}
DEFAULT_DB = _config["NOTION_DEFAULT_DB_NAME"]
'''
print 함수의 출력 버퍼를 즉시 플러시
'''
from sys import stdout
stdout.reconfigure(line_buffering = True)
'''
노션 동기화
'''
from env import *
from docker import from_env
from notion_client import Client
from argparse import ArgumentParser
from datetime import datetime, timezone, timedelta
'''
노션 클라이언트와 도커 클라이언트 초기화
'''
Notion = Client(auth = KEYS['NOTION_TOKEN'])
Docker = from_env()
'''
노션 데이터베이스 캐시 생성
'''
def create_notion_database_cache():
    notion_db_cache = {}
    #모든 노션 데이터베이스에 대해서 검색
    for db_name, db_id in DB.items():
        try:
            query_result = Notion.databases.query(database_id = db_id)
            results = query_result.get("results", [])
            db_list = {}
            for page in results:
                page_name = page['properties']['Name']['title'][0]['text']['content']
                db_list[page_name] = page
            notion_db_cache[db_name] = db_list
            print(f"[Success] Loaded Notion DB {db_name} with {len(db_list)} items")
        except Exception as e:
            print(f"[Failed] Querying Notion DB {db_name} : {e}")
            notion_db_cache[db_name] = {}
    return notion_db_cache
'''
노션 데이터베이스에서 컨테이너 정보가 위치한 DB 검색
'''
def get_notion_database_id(container, notion_db_cache):
    #모든 노션 데이터베이스에 대해서 검색
    for db_name, db_list in notion_db_cache.items():
        try:
            #컨테이너 이름으로 노션 데이터베이스에서 검색
            if container in db_list:
                db_page = db_list[container]
                return [db_page], db_name
        except Exception as e:
            print(f"[Failed] Querying Notion DB {db_name} for container {container}: {e}")
    #검색 결과가 없는 경우 기본 DB와 빈 리스트 반환
    return [], DEFAULT_DB
'''
컨테이너 정보를 수집하고 노션 데이터베이스 규격으로 변환
'''
def get_container_info(container):
    #컨테이너 IP와 포트 정보를 초기화
    container_ip = ''
    container_ports = ''
    #Host Network가 아닌 경우에만 IP 정보를 수집
    if container.attrs['HostConfig']['NetworkMode'] != 'host':
        networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
        if networks:
            for network_name, network_info in networks.items():
                container_ip = network_info.get('IPAddress', '')
    else:
        container_ip = 'host'
    #컨테이너의 포트 매핑 정보 수집
    ports = container.attrs['NetworkSettings'].get('Ports', {})
    for container_port, exposed_ports in ports.items():
        if exposed_ports:
            for mapping in exposed_ports:
                #Ipv4 주소에 매핑된 경우에만 포트 정보 수집
                if mapping.get('HostIp', '').startswith('0.'):
                    host_port = mapping.get('HostPort', '')
                    container_ports += f"{host_port}→{container_port}\n"
    if container_ports:
        container_ports = container_ports.rstrip('\n')
    else:
        container_ports = 'none'
    #노션 데이터베이스에 저장할 컨테이너 정보 생성
    properties = {}
    #컨테이너 이름
    properties['Name'] = {
        "title" : [
            {
                "text" : {
                    "content" : container.name
                }
            }
        ]
    }
    #컨테이너 상태
    properties['Status'] = {
        "status" : {
            "name" : container.status
        }
    }
    #컨테이너 IP
    properties['IP'] = {
        "rich_text" : [
            {
                "text" : {
                    "content" : container_ip
                }
            }
        ]
    }
    #컨테이너 포트
    if container_ip != 'host' and container.status != 'exited':
        properties["Ports"] = {
            "rich_text" : [
                {
                    "text" : {
                        "content" : container_ports
                    }
                }
            ]
        }
    #컨테이너 마지막 상태 변경 시간
    if container.status == 'running':
        properties["Seen"] = {
            "date" : {
                "start" : container.attrs['State']['StartedAt'],
                "end" : None
            }
        }
    else:
        properties["Seen"] = {
            "date" : {
                "start" : container.attrs['State']['FinishedAt'],
                "end" : None
            }
        }
    return properties
'''
노션 데이터베이스에 컨테이너 정보 갱신 혹은 추가
'''
def update_notion_database(db_page, db_name, container, properties):
    #아이템이 있는 경우 업데이트
    if db_page:
        try:
            print(f"[Success] Updating {container} in Notion DB {db_name}")
            Notion.pages.update(page_id = db_page[0]["id"], properties = properties)
        except Exception as e:
            print(f"[Failed] Updating Notion DB {db_name} for container {container}: {e}")
    #아이템이 없는 경우 새로 생성
    else:
        try:
            print(f"[Success] Creating {container} in Notion DB {db_name}")
            Notion.pages.create(parent = {"database_id" : DB[db_name]}, properties = properties)
        except Exception as e:
            print(f"[Failed] Creating Notion DB {db_name} for container {container}: {e}")
'''
모든 컨테이너 정보를 노션에 업데이트
'''
def update_notion(container, notion_db_cache):
    #도커 컨테이너 정보 갱신
    try:
        db_page, db_name = get_notion_database_id(container.name, notion_db_cache)
        properties = get_container_info(container)
        update_notion_database(db_page, db_name, container.name, properties)
    except Exception as e:
        print(f"[Failed] Processing container {container.name} : {e}")
'''
노션에만 존재하는 컨테이너 정보 archived 처리
'''
def archive_notion(container_name, notion_db_cache):
    #모든 노션 데이터베이스에 대해서 검색
    for db_name, db_list in notion_db_cache.items():
        try:
            if container_name in db_list:
                #노션에만 존재하는 컨테이너는 archived 처리
                print(f"[Success] Archiving {container_name} in Notion DB {db_name}")
                Notion.pages.update(
                    page_id = db_list[container_name]['id'],
                    properties = {
                        "Status" : {
                            "status" : {
                                "name" : "archived"
                            }
                        },
                        "Seen" : {
                            "date" : {
                                "start" : datetime.now(timezone(timedelta(hours = 9))).isoformat(),
                                "end" : None
                            }
                        },
                        "IP" : {
                            "rich_text" : [
                                {
                                    "text" : {
                                        "content" : ""
                                    }
                                }
                            ]
                        }
                    }
                )
        except Exception as e:
            print(f"[Failed] Archiving Notion DB {db_name} : {e}")
'''
메인 함수 : argparse를 사용하여 명령줄 인자 처리
'''
def main():
    #argparse를 사용하여 명령줄 인자 처리
    parser = ArgumentParser(description = "Update Docker container info to Notion")
    parser.add_argument('--sync', action = 'store_true', help = 'Sync Docker container info to Notion (overwrite existing data)')
    args = parser.parse_args()
    '''
    --sync 옵션이 있는 경우 노션 데이터베이스에 컨테이너 정보 갱신 (기존 데이터 덮어쓰기)
    --sync 옵션이 없는 경우 노션 데이터베이스에 변경사항 갱신 (기존 데이터 유지)
    '''
    if args.sync:
        print("[Info] Syncing Docker container into Notion...")
        #도커 컨테이너 정보 수집
        containers = Docker.containers.list(all = True)
        #노션 데이터베이스 캐시 생성
        notion_db_cache = create_notion_database_cache()
        #모든 컨테이너 정보를 노션 데이터베이스에 갱신
        for container in containers:
            update_notion(container, notion_db_cache)
        #노션 데이터베이스에 존재하지 않는 컨테이너 정보 archived 처리
        active_containers = [c.name for c in containers]
        for db_name in DB.keys():
            for container_name in notion_db_cache[db_name].keys():
                if container_name not in active_containers:
                    archive_notion(container_name, notion_db_cache)
    else:
        try:
            print("[Info] Updating Notion database with Docker container info...")
            #도커 이벤트 스트림을 통해 컨테이너 상태 변경 감지
            for event in Docker.events(decode = True):
                if event['Type'] != 'container':
                    continue
                #이벤트 타입에 따라 노션 데이터베이스 갱신
                action = event.get('Action')
                if action in ['start', 'stop', 'destroy']:
                    #노션 데이터베이스 캐시 생성
                    notion_db_cache = create_notion_database_cache()
                    if action == 'destroy':
                        #컨테이너가 삭제된 경우 노션 데이터베이스에서 archived 처리
                        container_name = event['Actor']['Attributes']['name']
                        archive_notion(container_name, notion_db_cache)
                    else:
                        #컨테이너가 시작되거나 중지된 경우 노션 데이터베이스 갱신
                        container_id = event.get('id')
                        try:
                            container = Docker.containers.get(container_id)
                            update_notion(container, notion_db_cache)
                        except Exception as e:
                            print(f"[Warning] Container {container_id} not found. Skip. : {e}")
        except KeyboardInterrupt:
            print("Exiting...")

if __name__ == '__main__':
    main()
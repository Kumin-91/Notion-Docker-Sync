# Notion Docker Sync

도커 컨테이너 상태를 Notion DB에 자동 동기화하는 Python 코드입니다.
`--sync` 옵션을 이용해 전체 동기화 (기존 내용까지 덮어씀) 가능하며, 실시간 감지도 지원합니다.

## 기능

- 컨테이너 상태 (running, exited, archived) 자동 기록
- 마지막 상태 변경 시간, IP, 포트 자동 기록
- 삭제된 컨테이너는 Notion DB 내에서 archived 상태로 표시 (노션에만 존재하는 항목에 대해서 수행)
- Notion DB 다중 구성 가능
- `.env` 통한 민감한 정보 관리

## 사용 방법

### 1. 환경 변수 설정

`.env` 파일 작성

```env
NOTION_TOKEN=your_notion_token
NOTION_DOCKER_DB_ID=3939
NOTION_JENKINS_DB_ID=3939
NOTION_GAMES_DB_ID=3939
NOTION_DEFAULT_DB_NAME="Docker"
```

### 2. [선택 사항] docker image 빌드

```
docker build -t notion-docker-sync .
```

### 3. 실행

전체 동기화 (기존 내용까지 덮어씀)
```bash
docker run \
  -v /var/run/docker.sock:/var/run/docker.sock \
  notion-docker-sync --sync
```
```bash
python3 main.py --sync
```

실시간 이벤트 감지
```bash
docker run -d \
  --name notion-docker-sync \
  -v /var/run/docker.sock:/var/run/docker.sock \
  notion-docker-sync
```
```bash
python3 main.py
```

## Notion DB 예시

<img src="https://github.com/user-attachments/assets/c32ddf5e-8f7a-45a6-a588-4093175b7495" />
<img src="https://github.com/user-attachments/assets/18ebc311-308e-4394-bca0-89a511f5fbf5" />

## 참고 사항

- Notion DB 페이지는 사전에 구성되어 있어야 하며, 컨테이너 이름을 기준으로 식별합니다.
- 자동 분류는 지원하지 않습니다.

## 목표

- [ ] 컨테이너 label 기반 신규 컨테이너 자동 분류
- [ ] 로그에 타임스탬프 추가
- [ ] 이미지 정보와 같은 추가 정보 연동

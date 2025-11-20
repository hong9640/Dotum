![image](image.png)

# 돋음 포팅 매뉴얼

# 목차

1. 개발 환경
2. 빌드 시 사용되는 환경 변수
3. 배포 시 특이사항

## 1. 개발 환경

### **Backend**

---

- Python 3.11 slim
- FastAPI 0.119.0
- Visual Studio Code

### **Frontend**

---

- Type Script
- Vite
- React 19.1
- Tailwind CSS

### **DB**

---

- PostgreSQL 15

### **Infra**

---

- AWS EC2(메인 서버)
- Google Cloud Platform VM(Wav2Lip, Omnilingual ASR)
- Google Cloud Storage
- ubuntu 22.04 LTS
- Docker
- Docker Compose
- Jenkins LTS

## 2. 빌드 시 사용되는 환경 변수

---

### 메인 서버
- 경로: `./.env` (프로젝트 루트 디렉토리)

```env
JWT_SECRET={openssl rand -base64 64로 발급받은 secret key}
DB_ID={데이터베이스 운영계정}
DB_PW={데이터베이스 운영 비밀번호}
DB_NAME={데이터베이스 스키마}
DB_PORT={데이터베이스 포트번호}
DB_NETWORK={docker-compose에 설정된 네트워크 기본값 : postgres}
DEBUG={디버그 표시 여부}
GCS_BUCKET_NAME={google cloud storage 버킷 이름}
GCS_PROJECT_ID={google cloud storage 프로젝트 ID}
GCS_CREDENTIALS_PATH=./credentials/key.json
CORS_ORIGINS={CORS URL : 도메인 주소 ex: https://www.example.com }
ML_SERVER_URL={인퍼런스 서버 URL ex: http://<인퍼런스서버IP>:8000}
STT_SERVER_URL={인퍼런스 서버 URL ex: http://<인퍼런스서버IP>:8080}
ELEVENLABS_API_KEY={ElevenLabs에서 발급받은 API 키}
ENABLE_WAV2LIP={서빙서버 사용 여부 기본값 : True}
OPEN_AI_API_KEY={OPEN AI에서 발급받은 API 키 (GPT 사용)}
VITE_BASE_URL={프론트엔드 API 기본 URL ex: https://www.example.com}
```

### 인퍼런스 서버
- 경로: `./serving-server/.env` (serving-server 디렉토리)

```env
GCP_PROJECT_ID={google cloud storage 프로젝트 ID}
GCS_BUCKET={google cloud storage 버킷 이름}
GCS_CREDENTIAL_PATH=./credentials/key.json
```

---

## 3. 배포 시 특이사항

### **인프라 설정**

1. 메인 서버 인스턴스 설정
	- 참고: 메인 서버의 경우 AWS로 생성된 인스턴스를 사용했음
	- AWS EC2 xlarge(lightsail)
	
   - 요구사항

   | CPU    | RAM  | SSD                    |
   | ------ | ---- | ---------------------- |
   | 4vCPUs | 16GB | 320GB SSD(필요시 확장) |

2. 인퍼런스 서버 인스턴스 설정
	- 참고: 인퍼런스 서버의 경우 Google Cloud의 Compute Engine 설정 방법을 기준으로 하고 있음

	- 요구사항

   | CPU                      | RAM  | SSD                    | GPU           |
   | ------------------------ | ---- | ---------------------- | ------------- |
   | n1-standard-4 (vCPU 4EA) | 15GB | 150GB SSD(필요시 확장) | NVIDIA T4 1EA |
   
   - 방화벽 설정
	   1. 방화벽 생성
		   - 좌측 상단 탐색메뉴 → `VPC 네트워크` → `방화벽` 클릭
		   - 우선순위: 999
		   - 방향: 인그레스
		   - 소스 필터
			   - IP 범위: 0.0.0.0/0
		   - 프로토콜 및 포트
			   - TCP:22, 8000, 8080, 55555
	   2. 생성된 방화벽 등록
		   - `네트워크 태그`에 생성한 방화벽 별칭을 등록
			   - 주의: **방화벽 이름이 아님**
   - 서버 주소 설정
	   - 고정된 서버 주소로 설정 필요
		 1. 좌측 상단 탐색메뉴 → `VPC 네트워크` → `IP 주소` 클릭 
		 2. `액세스 유형`이 `외부`인 항목에 `작업 보기` 클릭
		 3. `고정 IP 주소로 승급` 클릭

3. 버킷 설정
	- 참고: 버킷의 경우 Google Cloud의 Storage를 이용함
	- credentials key 발급 방법
		1. 서비스 계정 진입
			- 좌측 상단 탐색메뉴 → `IAM 및 관리자` → `서비스 계정` 클릭
		2. `서비스 계정 만들기`를 통해 서비스 계정 생성
		3. 생성된 서비스 계정에서 `작업` → `키 관리` 클릭
		4. `키 추가` 혹은 기타 작업으로 key.json 발급
	


### **프로젝트**

---

### **Main server**

1. git clone

- `git clone <REPO_URL>`
- `cd <project_name>`

2. 환경변수 파일 작성

- `touch .env`

3. 환경변수 등록

- `sudo vi .env`

- 환경변수 내용은 상단 참고

4. 프로젝트 실행

- `docker compose build`
- `docker compose up -d`

**만약 CI/CD를 통해 환경변수를 갱신할 경우**

- ubuntu 기준 : /home/user/.env 생성

### **serving server**

1. 인스턴스 접속 후 원격저장소에서 clone

- `git clone <REPO_URL>`

2. serving-server 폴더로 이동

- `cd serving-server`

3. 가상환경 생성
`python3 -m venv venv`

4. 가상환경 활성화
`source venv/bin/activate`

5. 라이브러리 설치
`pip3 install -r requirements.txt`

6. 서버 실행
`PORT=8000 nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &`

`PORT=8080 nohup uvicorn api.main:app --host 0.0.0.0 --port 8080 > server2.log 2>&1 &`

---

## Nginx

---

- nginx.conf 설정

```
# -------- 1. HTTP(80포트) --------
server {
  listen 80; # 80번 포트에서 들어오는 요청을 처리
  server_name <배포 URL>; # 이 설정이 적용될 도메인 지정
  return 301 https://$host$request_uri; # http요청이 오면 301응답을 반환하고 https로 리다이렉트. $request_uri는 요청된 경로 그대로 유지
}

# -------- 2. HTTPS(443포트) --------
server {
  listen 443 ssl; # 443번 포트에서 ssl을 사용해 요청을 처리
  server_name <배포 URL>; # 해당 server{}블록이 배포 URL로 들어온 요청을 처리하도록 지정
  
  client_max_body_size 100M; #업로드 가능한 용량 제한

  # SSL 인증서 경로 지정

  ssl_certificate /etc/letsencrypt/live/k13s201.p.ssafy.io/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/k13s201.p.ssafy.io/privkey.pem;

  location /api/ { # /api로 시작하는 모든 요청을 처리
    proxy_pass http://backend:8000/api/; #요청을 백엔드(8000포트)로 전달
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";

    if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' "$http_origin" always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization,Accept,Content-Type' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Content-Length' 0;
            add_header 'Content-Type' 'text/plain charset=UTF-8';
            return 204;
        }

    add_header 'Access-Control-Allow-Origin' "$http_origin" always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
  }

  location / { # / 요청을 처리
    root /usr/share/nginx/html; # 정적파일을 /usr/share/nginx/html에서 제공
    try_files $uri $uri/ /index.html; # 요청한 파일이 없으면 /index.html을 반환
    add_header Access-Control-Allow-Origin "<배포 URL>"; # cors허용
    add_header Access-Control-Allow-Credentials "true"; # 클라이언트가 쿠키포함요청을 보낼 수 있도록 설정
  }
}
```

- SSL 인증서 발급 방법 (letsEncrypt 기준)

1. certbot 설치

- `sudo apt-get update`
- `sudo apt-get install certbot`
- `sudo apt-get install python3-certbot-nginx`

2. SSL 인증서 발급

- `sudo certbot --nginx -d <도메인 주소> -d <도메인 주소>`

---

## Jenkins

---

1. Jenkins 계정 생성 및 권장 플러그인 설치

2. Jenkins Gitlab 플러그인 설치

3. 파이프라인 생성 
 - Triggers 설정
 - Push Event만 체크
 - Pipeline 설정
 - pipeline script from SCM (프로젝트에 있는 파이프라인 코드 사용)
 - SCM : Git
 - Repository URL : <.git으로 끝나는 git주소>
 - Credentials : <git 계정 입력>
 - Branch to Build : */master 형식으로 입력
 
4. credentials 등록
 - secret file 선택 후 GCS에서 발급받은 key.json 업로드
 

## 4. 외부 서비스

### OpenAI API

`https://platform.openai.com/api-keys`
 - 해당 경로에서 발급 후 키 등록
 
### ElevenLabs

`https://elevenlabs.io`
 - 해당 경로에서 발급 후 키 등록
 
  

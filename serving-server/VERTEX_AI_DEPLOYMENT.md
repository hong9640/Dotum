# Vertex AI 배포 가이드

Google Cloud Vertex AI에 Serving Server GPU 버전을 배포하는 가이드입니다.

## 📋 사전 준비

### 1. GCP 프로젝트 설정

```bash
export PROJECT_ID=your-project-id
export REGION=asia-northeast3
gcloud config set project $PROJECT_ID
```

### 2. API 활성화

```bash
gcloud services enable aiplatform.googleapis.com containerregistry.googleapis.com
```

## 🔨 배포 단계

### 1. Docker 이미지 빌드 및 푸시

```bash
export IMAGE_URI=gcr.io/$PROJECT_ID/serving-server-gpu:v3.0
docker build -t $IMAGE_URI .
docker push $IMAGE_URI
```

### 2. Vertex AI 모델 업로드

```bash
gcloud ai models upload \
  --region=$REGION \
  --display-name=serving-server-gpu \
  --container-image-uri=$IMAGE_URI \
  --container-health-route=/health \
  --container-predict-route=/api/v1/lip-video-optimized \
  --container-ports=8080
```

### 3. Endpoint 배포

```bash
gcloud ai endpoints deploy-model ENDPOINT_ID \
  --region=$REGION \
  --model=MODEL_ID \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --min-replica-count=1
```

자세한 내용은 [Vertex AI 문서](https://cloud.google.com/vertex-ai/docs)를 참조하세요.

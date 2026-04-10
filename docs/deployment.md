# 🚀 Deployment Guide (전체 배포 흐름)

## 1. 프로젝트 구조

- Django (Web API)
- FastAPI (AI 서버)
- Celery + Redis (비동기 처리)
- PostgreSQL (DB)
- Nginx (Reverse Proxy)

---

## 2. 배포 흐름

1. 로컬 개발 완료
2. GitHub push
3. GitHub Actions (CI 실행)
4. GitHub Actions (CD 실행)
5. EC2 SSH 접속
6. deploy.sh 실행
7. Docker 컨테이너 재시작

---

## 3. EC2 초기 세팅

bash
sudo apt update
sudo apt install docker.io docker-compose git -y
sudo usermod -aG docker ubuntu

---

## 4. 프로젝트 실행

bash
cd ~/product_review_service/backend
docker compose -f docker-compose.prod.yml up -d --build

---

## 5. 확인

bash
docker compose ps
docker compose logs --tail=100

---

## 6. 서비스 확인

- Django: http://EC2_IP/products/
- FastAPI: http://EC2_IP:8001

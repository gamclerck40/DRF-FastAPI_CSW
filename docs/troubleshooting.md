# 🔥 Troubleshooting (문제 해결 매뉴얼)

---

## 1. git pull 실패

### ❗ 에러

bash
Permission denied (publickey)

### 🔍 원인

- GitHub 인증 안됨

### ✅ 해결

bash
git remote -v
git pull origin main

---

## 2. Docker 권한 문제

### ❗ 에러

bash
permission denied while trying to connect to docker

### 🔍 원인

- docker 그룹 미등록

### ✅ 해결

bash
sudo usermod -aG docker ubuntu
newgrp docker
groups

---

## 3. 환경변수 누락

### ❗ 에러

bash
SECRET_KEY not found

### 🔍 원인

- .env 없음

### ✅ 해결

bash
ls -al
cat .env.prod

---

## 4. 경로 오류

### ❗ 에러

bash
No such file or directory

### 🔍 원인

- 경로 오타

### ✅ 해결

bash
pwd
ls

---

## 5. 컨테이너 실행 안됨

### 확인

bash
docker compose ps
docker compose logs --tail=100

---

## 6. 서비스 접속 안됨

### 확인 순서

1. docker 실행 상태
2. nginx 로그
3. EC2 보안 그룹 (80 포트)
4. ALLOWED_HOSTS 설정

---

## 💡 핵심 원칙

👉 에러 → 원인 → 해결 순서로 접근
👉 로그 먼저 확인

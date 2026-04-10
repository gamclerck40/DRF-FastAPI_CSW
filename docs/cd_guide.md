# ⚙️ CD (Continuous Deployment) 설정 가이드

## 1. 개념

- CI: 코드 테스트
- CD: 자동 배포
  👉 push → 자동 배포 구조

---

## 2. GitHub Secrets 설정

필수 값:

- EC2_HOST
- EC2_USERNAME
- EC2_SSH_KEY
- EC2_PORT

---

## 3. deploy.sh (EC2 내부)

bash
#!/bin/bash
set -e

cd /home/ubuntu/product_review_service/backend

echo "=== Git pull ==="
git pull origin main

echo "=== Docker build & up ==="
docker compose -f docker-compose.prod.yml up -d --build

echo "=== Clean images ==="
docker image prune -f

echo "Deploy Complete"

---

## 4. cd.yml

yaml
name: CD Deploy to EC2

on:
push:
branches: - main

jobs:
deploy:
runs-on: ubuntu-latest

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_KEY }}
          port: ${{ secrets.EC2_PORT }}
          script: |
            cd /home/ubuntu/product_review_service/backend
            ./deploy.sh

---

## 5. 동작 흐름

text
git push → GitHub Actions → SSH 접속 → deploy.sh 실행 → 배포 완료

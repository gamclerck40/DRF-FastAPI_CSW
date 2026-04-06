FROM python:3.12-slim
# → Python이 설치된 기본 환경 가져오기

WORKDIR /app
# → 컨테이너 내부 작업 폴더 설정

RUN apt-get update && apt-get install -y build-essential
# → 필요한 시스템 패키지 설치

COPY requirements.txt .
# → 라이브러리 목록 복사

RUN pip install -r requirements.txt
# → Python 패키지 설치

COPY . .
# → 프로젝트 전체 코드 복사

EXPOSE 8000
# → 컨테이너에서 사용할 포트 지정

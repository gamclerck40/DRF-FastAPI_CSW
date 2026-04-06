from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from api.recommend import router as recommend_router
from redis.asyncio import Redis
import json
import logging  # ✅ [추가] 로깅

# ✅ [추가] logger 생성
logger = logging.getLogger(__name__)


app = FastAPI(title="AI Recommendation Server")

REDIS_URL = "redis://redis:6379/0"

app.include_router(recommend_router)


@app.get("/")
def root():
    return {"message": "AI server is running"}


@app.websocket("/ws/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):

    # ✅ [추가] WebSocket 연결 요청 로그
    logger.info(f"[WS CONNECT] task_id={task_id}")

    await websocket.accept()

    redis = Redis.from_url(REDIS_URL)
    pubsub = redis.pubsub()
    channel_name = f"task_result_{task_id}"

    # ✅ [추가] Redis 구독 시작 로그
    logger.info(f"[REDIS SUBSCRIBE] channel={channel_name}")

    await pubsub.subscribe(channel_name)

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            raw_data = message["data"]

            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode("utf-8")

            # ✅ [추가] 메시지 수신 로그
            logger.info(f"[REDIS RECEIVE] task_id={task_id}")

            data = json.loads(raw_data)

            # ✅ [추가] 클라이언트 전송 로그
            logger.info(f"[WS SEND] task_id={task_id} status={data.get('status')}")

            await websocket.send_json(data)

            # 1회성 알림 후 종료
            break

    except WebSocketDisconnect:
        # ✅ [추가] 클라이언트 강제 종료 로그
        logger.warning(f"[WS DISCONNECT] task_id={task_id}")

    except Exception as e:
        # ✅ [추가] 에러 로그 (stack trace 포함)
        logger.exception(f"[WS ERROR] task_id={task_id} error={str(e)}")

    finally:
        # ✅ [추가] 정리 작업 로그
        logger.info(f"[WS CLEANUP] task_id={task_id}")

        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
        await redis.close()

        # 이미 끊긴 경우 예외 방지용 try
        try:
            await websocket.close()
        except Exception:
            pass

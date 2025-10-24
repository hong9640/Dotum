from fastapi import FastAPI

from api.core.config import settings
from api.core.middleware import register_middlewares
from api.service.dto import LipVideoGenerationRequest, LipVideoGenerationResponse

import time

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)

register_middlewares(app)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/v1/lip-video")
async def generate_lip_video(req: LipVideoGenerationRequest):
    start = time.time()
    # 1. GCS에서 다운로드
    # 2. FreeVC 실행 (subprocess)
    # 3. Wav2Lip 실행
    # 4. 결과 업로드
    # ...
    return LipVideoGenerationResponse(
        result_video_gs='',
        process_time_ms=(time.time() - start) * 1000
    )

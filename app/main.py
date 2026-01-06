from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.controllers import app

app = FastAPI()

# Mount static folder (nếu folder không có thì để trống cũng ok)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Import router và include
# (giữ nguyên cách import này — nếu có vòng import, ta sẽ thấy dấu hiệu trong log)
from app.routers import router
app.include_router(router)

# Debug: in danh sách route đã đăng ký
print(">>> main.py: registered routes on startup:")
for r in app.router.routes:
    try:
        print("   ", r.path)
    except Exception:
        # một vài route object không có path readable, bỏ qua
        pass

# Một route test trực tiếp trên main để đảm bảo server phản hồi
@app.get("/__ping")
def ping():
    return {"ok": True, "msg": "ping từ main"}

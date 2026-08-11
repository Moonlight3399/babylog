# ============================================================
# BabyLog - 应用入口
# ============================================================
from app import create_app
from config import PORT

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=PORT)

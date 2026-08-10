# ============================================================
# BabyLog - 应用入口
# ============================================================
from app import create_app, migrate_schema
from config import PORT

app = create_app()

if __name__ == '__main__':
    migrate_schema(app)
    app.run(debug=False, host='0.0.0.0', port=PORT)

# ============================================================
# BabyLog - 页面路由
# ============================================================
from flask import Blueprint, render_template

from .auth import login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index(user):
    return render_template('index.html', user=user)

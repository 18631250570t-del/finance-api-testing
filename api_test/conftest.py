import uuid

import pytest

from utils.api_client import get_token, post
from utils.assertions import assert_status




def _new_headers():                       # 普通函数（下划线开头，pytest 不当 fixture）
    email = f"u_{uuid.uuid4().hex[:8]}@qq.com"
    post("/register", {"email": email, "password": "12345678"})
    token = get_token(email, "12345678")
    return {"Authorization": "Bearer " + token}


@pytest.fixture
def auth_headers():                       # 用户 A
    return _new_headers()                 # 空1


@pytest.fixture
def other_headers():                      # 空2：给用户 B 起个名字
    return _new_headers()

@pytest.fixture
def seeded_headers():
    headers = _new_headers()          # 先造一个干净账号

    plan = [                          # 三笔数据的计划
        (100, "food", "2026-05-01T00:00:00"),
        (250, "food", "2026-05-15T10:00:00"),
        (50,  "transport", "2026-06-01T00:00:00"),
    ]
    for amount, category, date in plan:
        res = post("/transactions",
                   {"amount": amount, "category": category, "date": date},
                   headers=headers)
        assert_status(res, 201)       # 造数据失败要立刻报错，否则后面全是假失败

    return headers

@pytest.fixture
def registered_user():
    """一个已经注册好的用户，返回邮箱和密码（供登录测试用）"""
    email = f"u_{uuid.uuid4().hex[:8]}@qq.com"
    post("/register", {"email": email, "password": "12345678"})
    return {"email": email, "password": "12345678"}

@pytest.fixture
def budget(auth_headers):
    """创建一个预算，返回它的 id 和对应的请求头（供详情/更新/删除用例复用）"""
    res = post("/budgets", {"name": "测试预算", "limit": 1000}, headers=auth_headers)
    assert_status(res, 201)
    return {"id": res.json()["data"]["id"], "headers": auth_headers}
"""登录接口全量测试：凭证校验 + 未注册邮箱 + 字段校验"""
import pytest

from utils.api_client import post
from utils.assertions import assert_detail, assert_status


@pytest.mark.p1
@pytest.mark.parametrize(
    "password, status, detail",
    [
        ("wrong!23", 401, "Invalid credentials"),
        ("1234567", 401, "Invalid credentials"),
        ("", 401, "Invalid credentials"),
        ("12345678", 200, None),
    ],
    ids=["密码错误", "密码不匹配", "密码为空", "密码正确"],
)
def test_login_password(registered_user, password, status, detail):
    """用已注册用户测试各种密码 -> 401 或 200"""
    res = post("/login", {"email": registered_user["email"], "password": password})
    assert_status(res, status)
    if detail is None:
        assert res.json()["token_type"] == "bearer"
        assert len(res.json()["access_token"]) > 50
    else:
        assert_detail(res, detail)


@pytest.mark.p1
def test_login_unregistered_email():
    """邮箱没注册过 -> 401，且提示和「密码错」完全一样（防用户枚举）"""
    res = post("/login", {"email": "nobody_here_x@qq.com", "password": "12345678"})
    assert_status(res, 401)
    assert_detail(res, "Invalid credentials")


@pytest.mark.p1
@pytest.mark.parametrize(
    "payload, field",
    [
        ({"email": "a@b.com"}, "password"),
        ({"password": "12345678"}, "email"),
        ({"email": "bad", "password": "12345678"}, "email"),
        ({"email": "", "password": "12345678"}, "email"),
        ({"email": "a@b.com", "password": None}, "password"),
    ],
    ids=["缺password", "缺email", "邮箱无@", "邮箱空串", "密码为null"],
)
def test_login_validation(payload, field):
    """登录字段不合法 -> 422，且错误指向对应字段"""
    res = post("/login", payload)
    assert_status(res, 422)
    assert field in res.text, f"422 响应里没提到 {field}，实际：{res.text}"

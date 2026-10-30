"""注册接口完整测试：字段校验 / 长度边界 / 成功路径 / 重复注册"""
import uuid

import pytest

from utils.api_client import post
from utils.assertions import assert_detail, assert_status

PWD = "12345678"


def _unique_email(prefix="reg_"):
    """生成唯一邮箱，保证用例可重复执行"""
    return f"{prefix}{uuid.uuid4().hex[:8]}@qq.com"


# ============================================================
# ① 字段格式校验：11 条
# ============================================================
@pytest.mark.p1
@pytest.mark.parametrize(
    "payload, field",
    [
        ({"email": "bad", "password": PWD}, "email"),
        ({"email": "userexample.com", "password": PWD}, "email"),
        ({"email": "user@", "password": PWD}, "email"),
        ({"email": "a b@c.com", "password": PWD}, "email"),
        ({"email": "", "password": PWD}, "email"),
        ({"password": PWD}, "email"),
        ({"email": "a@b.com", "password": "1234567"}, "password"),
        ({"email": "a@b.com", "password": ""}, "password"),
        ({"email": "a@b.com", "password": None}, "password"),
        ({"email": "a@b.com", "password": 12345678}, "password"),
        ({"email": "a@b.com"}, "password"),
    ],
    ids=[
        "邮箱格式非法", "邮箱无@", "邮箱缺域名", "邮箱含空格", "邮箱空串", "缺email字段",
        "密码7位", "密码空串", "密码null", "密码是数字类型", "缺password字段",
    ],
)
def test_register_invalid(payload, field):
    """各种非法输入 -> 422，且错误指向对应字段"""
    res = post("/register", payload)
    assert_status(res, 422)
    assert field in res.text, f"422 响应里没提到 {field}，实际：{res.text}"


# ============================================================
# ② 密码长度边界：6 条
# ============================================================
@pytest.mark.p1
@pytest.mark.parametrize(
    "length, expected",
    [
        (7, 422),      # 边界外（少一位）
        (8, 201),      # 边界上
        (9, 201),      # 边界内
        (72, 201),     # bcrypt 实际处理上限
        (100, 201),    # 仍接受
        (4096, 201),   # passlib 硬上限，刚好通过
    ],
    ids=["密码7位-拒绝", "密码8位-通过", "密码9位-通过",
         "密码72位-通过", "密码100位-通过", "密码4096位-通过"],
)
def test_password_length_boundary(length, expected):
    """密码长度边界：最少 8 位；上限 4096（超过会 500，见已知缺陷 #2）"""
    res = post("/register", {"email": _unique_email("pwd_"), "password": "a" * length})
    assert_status(res, expected)


# ============================================================
# ③ 邮箱格式非法：6 条（都返回 422，不写库，可用固定值）
# ============================================================
@pytest.mark.p2
@pytest.mark.parametrize(
    "email_value",
    [
        "@qq.com",                     # 没有 local 部分
        "a@b",                         # 没有域名后缀
        ".abc@qq.com",                 # 以点开头
        "a" * 248 + "@qq.com",         # 总长 255，超过 254 上限
        "a@b@qq.com",                  # 两个 @
        "." * 10 + "@qq.com",          # local 全是点
    ],
    ids=["无local部分", "无域名后缀", "以点开头", "总长255超限", "两个@号", "local全点号"],
)
def test_email_format_invalid(email_value):
    """邮箱格式或长度不合法 -> 422"""
    res = post("/register", {"email": email_value, "password": PWD})
    assert_status(res, 422)


# ============================================================
# ④ 邮箱长度边界（该通过的）：3 条
# ============================================================
@pytest.mark.p2
def test_email_local_part_64_ok():
    """local 部分正好 64 字符（RFC 上限）-> 通过"""
    local = "a" * 56 + uuid.uuid4().hex[:8]
    assert len(local) == 64
    res = post("/register", {"email": local + "@qq.com", "password": PWD})
    assert_status(res, 201)


@pytest.mark.p2
def test_email_local_part_65_accepted():
    """实测记录：local 65 字符超过 RFC 上限，但服务端接受（低危，见缺陷清单 #3）"""
    local = "a" * 57 + uuid.uuid4().hex[:8]
    assert len(local) == 65
    res = post("/register", {"email": local + "@qq.com", "password": PWD})
    assert_status(res, 201)


@pytest.mark.p2
def test_email_total_length_254_ok():
    """邮箱总长正好 254 字符（上限）-> 通过"""
    local = "a" * 239 + uuid.uuid4().hex[:8]
    email = local + "@qq.com"
    assert len(email) == 254
    res = post("/register", {"email": email, "password": PWD})
    assert_status(res, 201)


# ============================================================
# ⑤ 成功路径：2 条
# ============================================================
@pytest.mark.p0
def test_register_ok():
    """正常注册 -> 201，且响应不回传密码"""
    res = post("/register", {"email": _unique_email(), "password": PWD})
    assert_status(res, 201)
    assert res.json()["message"] == "User created"
    assert "password" not in res.json()


@pytest.mark.p1
def test_register_with_extra_field_ignored():
    """请求体塞未知字段 role=admin -> 被忽略，不会提权"""
    res = post("/register", {"email": _unique_email("ex_"), "password": PWD, "role": "admin"})
    assert_status(res, 201)
    assert "role" not in res.json()


# ============================================================
# ⑥ 重复注册：1 条
# ============================================================
@pytest.mark.p0
def test_register_duplicate_email(registered_user):
    """同一邮箱注册两次 -> 400（业务规则拒绝，不是 422）"""
    res = post("/register", {"email": registered_user["email"], "password": "another!234"})
    assert_status(res, 400)
    assert_detail(res, "User already exists")
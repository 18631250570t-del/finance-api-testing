"""已知缺陷登记簿

每条都是「期望 X，实际 Y」，用 xfail(strict=True) 固化：
  - 现在：显示 XFAIL，不拖累回归结果
  - 修好之后：显示 XPASS 并报错，提醒把标记删掉（防止标记腐烂）

缺陷清单
------------------------------------------------------------
#1  bcrypt 只处理前 72 字节，超长密码被截断，不同密码可互相登录   [中-高]
#2  密码超过 4096 位时 passlib 抛 PasswordSizeError 未捕获 -> 500  [中]
#3  金额无上限校验，1e308 可创建                                 [中]
#4  金额累加溢出导致 /stats 的 total_expenses 返回 null           [中]
#5  date 无范围校验，可记公元 1 年 / 9999 年 / 任意未来日期         [中]
#6  金额用 float 累加，0.1 + 0.2 != 0.3                          [中]
------------------------------------------------------------
"""
import uuid

import pytest

from utils.api_client import get, post
from utils.assertions import assert_status


def _unique_email(prefix="df_"):
    return f"{prefix}{uuid.uuid4().hex[:8]}@qq.com"


# ============================================================
# 缺陷 #1：bcrypt 72 字节截断
# ============================================================
@pytest.mark.xfail(strict=True,
                   reason="缺陷#1：bcrypt 只处理前 72 字节，超长密码被截断，不同密码可互相登录")
def test_long_password_should_not_login():
    """期望：不同密码登录必须 401。实际：200（截断导致两个密码等价）"""
    base = "a" * 72
    email = _unique_email("bc_")

    post("/register", {"email": email, "password": base + "XXXX"})
    res = post("/login", {"email": email, "password": base + "YYYY"})

    assert_status(res, 401)


# ============================================================
# 缺陷 #2：密码超 4096 位导致 500
# ============================================================
@pytest.mark.xfail(strict=True,
                   reason="缺陷#2：密码超过 4096 位时 passlib 抛异常未捕获，返回 500 而非 422")
def test_password_4097_should_be_422():
    """期望：超长密码应返回 422。实际：500（未捕获异常）"""
    res = post("/register", {"email": _unique_email("big_"), "password": "a" * 4097})

    assert_status(res, 422)


# ============================================================
# 缺陷 #3：金额无上限
# ============================================================
@pytest.mark.xfail(strict=True,
                   reason="缺陷#3：金额无上限校验，1e308 可创建（业务上应限制在合理范围）")
def test_amount_should_have_upper_limit(auth_headers):
    """期望：超过合理上限应返回 422。实际：201"""
    res = post("/transactions",
               {"amount": 1e308, "category": "huge"},
               headers=auth_headers)

    assert_status(res, 422)


# ============================================================
# 缺陷 #4：金额溢出导致统计为 null
# ============================================================
@pytest.mark.xfail(strict=True,
                   reason="缺陷#4：金额累加溢出导致 /stats 的 total_expenses 返回 null，违反契约")
def test_stats_total_should_not_be_null(auth_headers):
    """期望：total_expenses 应是数字。实际：null（1e308 + 1e308 溢出为 inf）"""
    for _ in range(2):
        post("/transactions",
             {"amount": 1e308, "category": "huge"},
             headers=auth_headers)

    res = get("/stats", headers=auth_headers)
    assert_status(res, 200)
    body = res.json()
    assert body["total_expenses"] is not None, f"统计返回了 null！响应：{body}"


# ============================================================
# 缺陷 #5：日期无范围校验
# ============================================================
@pytest.mark.xfail(strict=True,
                   reason="缺陷#5：date 无范围校验，可记公元 1 年 / 9999 年 / 任意未来日期")
def test_date_should_have_reasonable_range(auth_headers):
    """期望：超出合理范围（早于 2000 或晚于今天）应返回 422。实际：201"""
    res = post("/transactions",
               {"amount": 10, "category": "dt", "date": "1900-01-01T00:00:00"},
               headers=auth_headers)

    assert_status(res, 422)


# ============================================================
# 缺陷 #6：金额 float 精度漂移
# ============================================================
@pytest.mark.xfail(strict=True,
                   reason="缺陷#6：金额用 float 累加，0.1 + 0.2 != 0.3")
def test_stats_amount_precision(auth_headers):
    """期望：0.1 + 0.2 的合计精确等于 0.3。实际：0.30000000000000004"""
    post("/transactions", {"amount": 0.1, "category": "prec"}, headers=auth_headers)
    post("/transactions", {"amount": 0.2, "category": "prec"}, headers=auth_headers)

    res = get("/stats", headers=auth_headers)
    assert_status(res, 200)
    assert res.json()["total_expenses"] == 0.3, (
        f"实际合计：{res.json()['total_expenses']}"
    )

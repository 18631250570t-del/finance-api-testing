"""交易创建接口 POST /transactions 的完整校验测试

分两组：
  组 A（11 条）：各种非法输入 → 应该 422
  组 B（ 5 条）：边界该成功的 + 属主越权 → 应该 201 且行为正确
"""
import pytest

from utils.api_client import get, post
from utils.assertions import assert_status


# ============================================================
# 组 A：11 条「该被拒绝的」→ 422
# ============================================================
@pytest.mark.p1
@pytest.mark.parametrize(
    "payload, field",
    [
        # ---------- 金额：5 种非法 ----------
        ({"amount": 0, "category": "food"}, "amount"),
        ({"amount": -50, "category": "food"}, "amount"),
        ({"amount": None, "category": "food"}, "amount"),
        ({"amount": "abc", "category": "food"}, "amount"),
        ({"category": "food"}, "amount"),
        # ---------- 分类：4 种非法 ----------
        ({"amount": 10, "category": ""}, "category"),
        ({"amount": 10}, "category"),
        ({"amount": 10, "category": "x" * 101}, "category"),
        ({"amount": 10, "category": 123}, "category"),
        # ---------- 日期：1 种非法 ----------
        ({"amount": 10, "category": "food", "date": "2026/13/45"}, "date"),
        # ---------- 整个请求体为空 ----------
        ({}, "amount"),
    ],
    ids=[
        "金额为0",
        "金额为负",
        "金额为null",
        "金额非数字",
        "缺金额字段",
        "分类空串",
        "缺分类字段",
        "分类101字符",
        "分类是数字类型",
        "日期格式非法",
        "空请求体",
    ],
)
def test_create_transaction_invalid(auth_headers, payload, field):
    """参数不合法 → 422，且错误必须指向对应字段"""
    res = post("/transactions", payload, headers=auth_headers)
    assert_status(res, 422)
    assert field in res.text, f"422 响应里没提到字段 {field}，实际：{res.text}"


# ============================================================
# 组 B：5 条「边界内该成功」+「属主越权」
# ============================================================
@pytest.mark.p2
def test_create_amount_min_valid(auth_headers):
    """金额 0.001 —— 大于 0 的最小有效值，应该创建成功"""
    res = post("/transactions", {"amount": 0.001, "category": "tiny"}, headers=auth_headers)
    assert_status(res, 201)
    assert res.json()["amount"] == 0.001


@pytest.mark.p2
def test_create_amount_huge_accepted(auth_headers):
    """实测记录：金额没有上限校验，1e308 仍可创建（观察项，见缺陷清单 #3）"""
    res = post("/transactions", {"amount": 1e308, "category": "huge"}, headers=auth_headers)
    assert_status(res, 201)
    assert res.json()["amount"] == 1e308


@pytest.mark.p2
def test_create_category_min_length(auth_headers):
    """分类只有 1 个字符 —— 长度下限内，应该创建成功"""
    res = post("/transactions", {"amount": 10, "category": "x"}, headers=auth_headers)
    assert_status(res, 201)
    assert res.json()["category"] == "x"


@pytest.mark.p2
def test_create_category_max_length(auth_headers):
    """分类刚好 100 字符 —— 长度上限内，应该创建成功且不被截断"""
    category = "x" * 100
    res = post("/transactions", {"amount": 10, "category": category}, headers=auth_headers)
    assert_status(res, 201)
    assert res.json()["category"] == category

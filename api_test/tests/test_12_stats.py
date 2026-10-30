"""统计接口 GET /stats 测试

接口行为：
  GET /stats                统计全部交易
  GET /stats?month=YYYY-MM  只统计该月
  返回 {"total_expenses": 合计, "total_number": 笔数, "max_amount": 单笔最大}

复用 conftest 的 seeded_headers（3 笔固定交易）：
  100 元 food       2026-05-01
  250 元 food       2026-05-15
  50  元 transport  2026-06-01
  合计 400 / 3 笔 / 最大 250
"""
import pytest

from utils.api_client import delete, get, post
from utils.assertions import assert_detail, assert_status


# ============================================================
# A. 基础统计：5 条
# ============================================================
@pytest.mark.p0
def test_stats_empty(auth_headers):
    """新用户没有任何交易 -> 三个字段全是 0（不是 null、不是 404）"""
    res = get("/stats", headers=auth_headers)
    assert_status(res, 200)
    assert res.json() == {
        "total_expenses": 0,
        "total_number": 0,
        "max_amount": 0,
    }


@pytest.mark.p0
def test_stats_single(auth_headers):
    """只有一笔交易 -> 合计=最大=该笔金额，笔数=1"""
    post("/transactions", {"amount": 88, "category": "food"}, headers=auth_headers)

    res = get("/stats", headers=auth_headers)
    assert_status(res, 200)
    body = res.json()
    assert body["total_expenses"] == 88
    assert body["total_number"] == 1
    assert body["max_amount"] == 88


@pytest.mark.p0
def test_stats_multiple_total(seeded_headers):
    """3 笔交易 -> 合计 400、笔数 3"""
    res = get("/stats", headers=seeded_headers)
    assert_status(res, 200)
    body = res.json()
    assert body["total_expenses"] == 400
    assert body["total_number"] == 3


@pytest.mark.p1
def test_stats_max_is_single_not_sum(seeded_headers):
    """max_amount 是「单笔最大值」不是合计（250，不是 400）"""
    res = get("/stats", headers=seeded_headers)
    assert_status(res, 200)
    assert res.json()["max_amount"] == 250


@pytest.mark.p1
def test_stats_field_types(seeded_headers):
    """字段类型：total_number 是整数，金额是数字，且恰好只有这三个字段"""
    res = get("/stats", headers=seeded_headers)
    assert_status(res, 200)
    body = res.json()

    assert isinstance(body["total_number"], int)
    assert isinstance(body["total_expenses"], (int, float))
    assert isinstance(body["max_amount"], (int, float))
    assert set(body.keys()) == {"total_expenses", "total_number", "max_amount"}


# ============================================================
# B. 按月统计：3 条
# ============================================================
@pytest.mark.p0
def test_stats_by_month(seeded_headers):
    """按月统计：2026-05 有 2 笔，合计 350，最大 250"""
    res = get("/stats?month=2026-05", headers=seeded_headers)
    assert_status(res, 200)
    body = res.json()
    assert body["total_expenses"] == 350
    assert body["total_number"] == 2
    assert body["max_amount"] == 250


@pytest.mark.p1
def test_stats_month_without_data(seeded_headers):
    """指定一个没有数据的月份 -> 全 0（不是 404）"""
    res = get("/stats?month=2025-01", headers=seeded_headers)
    assert_status(res, 200)
    assert res.json()["total_number"] == 0
    assert res.json()["total_expenses"] == 0


@pytest.mark.p0
def test_stats_month_boundary(auth_headers):
    """月份边界：5月1日0点、5月31日23:59 计入；6月1日0点排除"""
    post("/transactions", {"amount": 10, "category": "b", "date": "2026-05-01T00:00:00"},
         headers=auth_headers)
    post("/transactions", {"amount": 20, "category": "b", "date": "2026-05-31T23:59:59"},
         headers=auth_headers)
    post("/transactions", {"amount": 40, "category": "b", "date": "2026-06-01T00:00:00"},
         headers=auth_headers)

    res = get("/stats?month=2026-05", headers=auth_headers)
    assert_status(res, 200)
    body = res.json()
    assert body["total_number"] == 2, f"5 月应只有 2 笔，实际 {body}"
    assert body["total_expenses"] == 30


# ============================================================
# C. 用户隔离：2 条
# ============================================================
@pytest.mark.p0
def test_stats_isolation_single(seeded_headers, other_headers):
    """A 的 400 元不能算进 B 的统计"""
    res = get("/stats", headers=other_headers)
    assert_status(res, 200)
    assert res.json()["total_expenses"] == 0
    assert res.json()["total_number"] == 0


@pytest.mark.p0
def test_stats_isolation_independent(auth_headers, other_headers):
    """两个用户各自有数据，互不影响"""
    post("/transactions", {"amount": 111, "category": "a"}, headers=auth_headers)
    post("/transactions", {"amount": 222, "category": "b"}, headers=other_headers)
    post("/transactions", {"amount": 333, "category": "b"}, headers=other_headers)

    a = get("/stats", headers=auth_headers).json()
    b = get("/stats", headers=other_headers).json()

    assert a["total_expenses"] == 111 and a["total_number"] == 1
    assert b["total_expenses"] == 555 and b["total_number"] == 2


# ============================================================
# D. 数据同步：3 条
# ============================================================
@pytest.mark.p0
def test_stats_after_create(auth_headers):
    """新增交易后，统计同步增加"""
    post("/transactions", {"amount": 100, "category": "food"}, headers=auth_headers)
    assert get("/stats", headers=auth_headers).json()["total_expenses"] == 100

    post("/transactions", {"amount": 88, "category": "food"}, headers=auth_headers)
    body = get("/stats", headers=auth_headers).json()
    assert body["total_expenses"] == 188
    assert body["total_number"] == 2


@pytest.mark.p0
def test_stats_after_delete(auth_headers):
    """删除交易后，统计同步减少"""
    first = post("/transactions", {"amount": 100, "category": "food"}, headers=auth_headers)
    post("/transactions", {"amount": 200, "category": "food"}, headers=auth_headers)

    assert get("/stats", headers=auth_headers).json()["total_expenses"] == 300

    delete(f"/transactions/{first.json()['id']}", headers=auth_headers)

    body = get("/stats", headers=auth_headers).json()
    assert body["total_expenses"] == 200
    assert body["total_number"] == 1
    assert body["max_amount"] == 200


@pytest.mark.p1
def test_stats_consistent_with_list(seeded_headers):
    """统计口径必须和列表一致：笔数、合计、最大值都对得上"""
    stats = get("/stats", headers=seeded_headers).json()
    rows = get("/transactions", headers=seeded_headers).json()

    assert stats["total_number"] == len(rows)
    assert stats["total_expenses"] == sum(r["amount"] for r in rows)
    assert stats["max_amount"] == max(r["amount"] for r in rows)


# ============================================================
# E. 参数校验：2 条
# ============================================================
@pytest.mark.p1
def test_stats_month_invalid_13(seeded_headers):
    """月份 13 —— /transactions 返回 400，/stats 实测返回 200 全 0（规则不一致）"""
    res = get("/stats?month=2026-13", headers=seeded_headers)
    assert_status(res, 200)
    assert res.json()["total_number"] == 0


@pytest.mark.p1
def test_stats_month_missing_part(seeded_headers):
    """month 只有年份（缺月份段）-> 400"""
    res = get("/stats?month=2026", headers=seeded_headers)
    assert_status(res, 400)
    assert_detail(res, "month must be in YYYY-MM format")

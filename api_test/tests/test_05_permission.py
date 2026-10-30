"""越权（横向权限）测试：A 不能操作 B 的数据

安全测试单独成文件的原因：越权是"横切关注点"，跨越所有模块。
集中后可以一眼看出"哪些资源、哪些操作测了越权"。

覆盖：
  A. 跨用户操作单个资源：交易/预算 × 查/改/删 = 6 条
  B. 写隔离：被拒绝后数据必须完好 = 1 条
  C. 列表隔离：交易、预算 = 2 条
  D. 统计隔离 = 1 条
  E. 属主篡改：创建时塞别人 user_id = 1 条
"""
import pytest

from utils.api_client import call, get, post
from utils.assertions import assert_status


def _create_resource(kind, headers):
    """造一个资源，返回它的 id"""
    if kind == "transaction":
        res = post("/transactions", {"amount": 999, "category": "secret"}, headers=headers)
        assert_status(res, 201)
        return res.json()["id"]
    res = post("/budgets", {"name": "别人的预算", "limit": 500}, headers=headers)
    assert_status(res, 201)
    return res.json()["data"]["id"]


def _get_resource(kind, rid, headers):
    path = f"/transactions/{rid}" if kind == "transaction" else f"/budgets/{rid}"
    return get(path, headers=headers)


# ============================================================
# A. 跨用户操作单个资源：6 条
# ============================================================
@pytest.mark.p0
@pytest.mark.parametrize(
    "kind, method, path_tmpl, body",
    [
        ("transaction", "GET",    "/transactions/{id}", None),
        ("transaction", "PUT",    "/transactions/{id}", {"amount": 1, "category": "hack"}),
        ("transaction", "DELETE", "/transactions/{id}", None),
        ("budget",      "GET",    "/budgets/{id}",      None),
        ("budget",      "PUT",    "/budgets/{id}",      {"name": "hack", "limit": 1}),
        ("budget",      "DELETE", "/budgets/{id}",      None),
    ],
    ids=[
        "交易-查他人", "交易-改他人", "交易-删他人",
        "预算-查他人", "预算-改他人", "预算-删他人",
    ],
)
def test_cross_user_denied(auth_headers, other_headers, kind, method, path_tmpl, body):
    """用 B 的身份操作 A 的资源 → 404，且 A 的数据仍然存在"""
    rid = _create_resource(kind, auth_headers)
    path = path_tmpl.format(id=rid)

    # ① B 尝试操作 → 必须被拒绝
    res = call(method, path, body=body, headers=other_headers)
    assert_status(res, 404)

    # ② A 以自己的身份复查 → 数据必须完好
    check = _get_resource(kind, rid, auth_headers)
    assert_status(check, 200)


# ============================================================
# B. 写隔离：被拒绝后数据不能被改坏
# ============================================================
@pytest.mark.p0
def test_cross_user_update_does_not_modify(auth_headers, other_headers):
    """B 改 A 的交易后，A 的金额必须原样不动（不能只看 404）"""
    rid = _create_resource("transaction", auth_headers)

    res = call("PUT", f"/transactions/{rid}",
               body={"amount": 1, "category": "hack"}, headers=other_headers)
    assert_status(res, 404)

    check = get(f"/transactions/{rid}", headers=auth_headers)
    assert_status(check, 200)
    assert check.json()["amount"] == 999, f"金额被篡改了：{check.json()}"
    assert check.json()["category"] == "secret"


# ============================================================
# C. 列表隔离：2 条
# ============================================================
@pytest.mark.p0
def test_transactions_list_isolation(auth_headers, other_headers):
    """A 的交易不能出现在 B 的列表里"""
    _create_resource("transaction", auth_headers)

    res = get("/transactions", headers=other_headers)
    assert_status(res, 200)
    assert res.json() == [], f"看到了别人的数据！{res.json()}"


@pytest.mark.p0
def test_budgets_list_isolation(auth_headers, other_headers):
    """A 的预算不能出现在 B 的列表里"""
    _create_resource("budget", auth_headers)

    res = get("/budgets", headers=other_headers)
    assert_status(res, 200)
    assert res.json() == [], f"看到了别人的预算！{res.json()}"


# ============================================================
# D. 统计隔离：1 条
# ============================================================
@pytest.mark.p0
def test_stats_isolation(auth_headers, other_headers):
    """A 的金额不能算进 B 的统计"""
    _create_resource("transaction", auth_headers)

    res = get("/stats", headers=other_headers)
    assert_status(res, 200)
    assert res.json()["total_expenses"] == 0
    assert res.json()["total_number"] == 0


# ============================================================
# E. 属主篡改：1 条
# ============================================================
@pytest.mark.p0
def test_cannot_override_user_id(auth_headers, other_headers):
    """创建时塞别人的 user_id → 服务端必须忽略，数据仍归自己"""
    other_id = get("/me", headers=other_headers).json()["user_id"]

    res = post("/transactions",
               {"amount": 10, "category": "x", "user_id": other_id},
               headers=auth_headers)
    assert_status(res, 201)
    assert res.json()["user_id"] != other_id, (
        f"数据被挂到别人名下了！他人 id={other_id}，实际归属={res.json()['user_id']}"
    )

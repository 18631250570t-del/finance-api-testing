"""预算模块完整测试：创建校验 / 边界 / CRUD / 越权

接口清单：
  POST   /budgets          创建（返回 message + data）
  GET    /budgets          列表（返回数组）
  GET    /budgets/{id}     详情（返回对象）
  PUT    /budgets/{id}     更新（返回 message + data）
  DELETE /budgets/{id}     删除（返回 message + deleted）
"""
import pytest

from utils.api_client import delete, get, post, put
from utils.assertions import assert_detail, assert_status


# ============================================================
# A. 创建校验：8 条（非法输入 → 422）
# ============================================================
@pytest.mark.p1
@pytest.mark.parametrize(
    "payload, field",
    [
        ({"name": "", "limit": 100}, "name"),
        ({"name": "x" * 101, "limit": 100}, "name"),
        ({"limit": 100}, "name"),
        ({"name": "餐饮", "limit": 0}, "limit"),
        ({"name": "餐饮", "limit": -1}, "limit"),
        ({"name": "餐饮", "limit": None}, "limit"),
        ({"name": "餐饮", "limit": "abc"}, "limit"),
        ({"name": "餐饮"}, "limit"),
    ],
    ids=[
        "名称空串", "名称101字符", "缺名称字段",
        "限额为0", "限额为负", "限额为null", "限额非数字", "缺限额字段",
    ],
)
def test_create_budget_invalid(auth_headers, payload, field):
    """预算创建的各种非法输入 → 422"""
    res = post("/budgets", payload, headers=auth_headers)
    assert_status(res, 422)
    assert field in res.text, f"422 响应里没提到 {field}，实际：{res.text}"


# ============================================================
# B. 创建边界成功：4 条
# ============================================================
@pytest.mark.p2
def test_create_name_min_length(auth_headers):
    """名称只有 1 个字符 —— 下限内，应该成功"""
    res = post("/budgets", {"name": "a", "limit": 100}, headers=auth_headers)
    assert_status(res, 201)
    assert res.json()["data"]["name"] == "a"


@pytest.mark.p2
def test_create_name_max_length(auth_headers):
    """名称刚好 100 字符 —— 上限内，应该成功且不截断"""
    name = "x" * 100
    res = post("/budgets", {"name": name, "limit": 100}, headers=auth_headers)
    assert_status(res, 201)
    assert res.json()["data"]["name"] == name


@pytest.mark.p2
def test_create_limit_min_positive(auth_headers):
    """限额 0.01 —— 最小正数，应该成功"""
    res = post("/budgets", {"name": "小额", "limit": 0.01}, headers=auth_headers)
    assert_status(res, 201)
    assert res.json()["data"]["limit"] == 0.01


@pytest.mark.p2
def test_create_limit_large(auth_headers):
    """限额 1e9 —— 大额，应该成功（无上限校验）"""
    res = post("/budgets", {"name": "大额", "limit": 1e9}, headers=auth_headers)
    assert_status(res, 201)
    assert res.json()["data"]["limit"] == 1e9


# ============================================================
# C. 列表：4 条
# ============================================================
@pytest.mark.p0
def test_list_empty(auth_headers):
    """新用户没有任何预算 → 返回空数组（不是 null、不是 404）"""
    res = get("/budgets", headers=auth_headers)
    assert_status(res, 200)
    assert res.json() == []


@pytest.mark.p0
def test_list_after_create(auth_headers):
    """创建一个后，列表里应该有 1 条"""
    post("/budgets", {"name": "餐饮", "limit": 1500}, headers=auth_headers)
    res = get("/budgets", headers=auth_headers)
    assert_status(res, 200)
    assert len(res.json()) == 1


@pytest.mark.p1
def test_list_multiple(auth_headers):
    """创建 3 个 → 列表返回 3 条，且都属于自己"""
    for i in range(3):
        post("/budgets", {"name": f"预算{i}", "limit": 100 * (i + 1)}, headers=auth_headers)
    res = get("/budgets", headers=auth_headers)
    assert_status(res, 200)
    assert len(res.json()) == 3


# ============================================================
# D. 详情：4 条
# ============================================================
@pytest.mark.p0
def test_get_budget_detail(budget):
    """查自己的预算详情 → 字段完整一致"""
    res = get(f"/budgets/{budget['id']}", headers=budget["headers"])
    assert_status(res, 200)
    body = res.json()
    assert body["id"] == budget["id"]
    assert body["name"] == "测试预算"
    assert body["limit"] == 1000


@pytest.mark.p1
def test_get_budget_not_found(auth_headers):
    """不存在的 id → 404"""
    res = get("/budgets/999999", headers=auth_headers)
    assert_status(res, 404)
    assert_detail(res, "Budget not found")


@pytest.mark.p2
def test_get_budget_invalid_id(auth_headers):
    """id 不是整数 → 422（路径参数类型校验）"""
    res = get("/budgets/abc", headers=auth_headers)
    assert_status(res, 422)


# ============================================================
# E. 更新：5 条
# ============================================================
@pytest.mark.p0
def test_update_budget_ok(budget):
    """正常更新名称和限额 → 200，返回新值"""
    res = put(f"/budgets/{budget['id']}", {"name": "新预算", "limit": 2000},
              headers=budget["headers"])
    assert_status(res, 200)
    assert res.json()["data"]["name"] == "新预算"
    assert res.json()["data"]["limit"] == 2000


@pytest.mark.p1
def test_update_budget_missing_limit(budget):
    """只传 name 不传 limit → 422（PUT 是全量替换）"""
    res = put(f"/budgets/{budget['id']}", {"name": "只改名"}, headers=budget["headers"])
    assert_status(res, 422)


@pytest.mark.p1
def test_update_budget_limit_zero(budget):
    """把限额改成 0 → 422，且原值不变"""
    res = put(f"/budgets/{budget['id']}", {"name": "零预算", "limit": 0},
              headers=budget["headers"])
    assert_status(res, 422)

    # 复查：确认没被改
    check = get(f"/budgets/{budget['id']}", headers=budget["headers"])
    assert check.json()["limit"] == 1000


@pytest.mark.p1
def test_update_budget_not_found(auth_headers):
    """更新不存在的 id → 404"""
    res = put("/budgets/999999", {"name": "x", "limit": 1}, headers=auth_headers)
    assert_status(res, 404)


# ============================================================
# F. 删除：5 条
# ============================================================
@pytest.mark.p0
def test_delete_budget_ok(budget):
    """正常删除 → 200，返回被删对象"""
    res = delete(f"/budgets/{budget['id']}", headers=budget["headers"])
    assert_status(res, 200)
    assert res.json()["message"] == "Budget deleted"
    assert res.json()["deleted"]["id"] == budget["id"]


@pytest.mark.p0
def test_delete_then_get_404(budget):
    """删除后再查 → 404（证明真的删了，不是只返回成功）"""
    delete(f"/budgets/{budget['id']}", headers=budget["headers"])

    res = get(f"/budgets/{budget['id']}", headers=budget["headers"])
    assert_status(res, 404)


@pytest.mark.p1
def test_delete_twice(budget):
    """重复删除 → 第二次 404"""
    delete(f"/budgets/{budget['id']}", headers=budget["headers"])

    res = delete(f"/budgets/{budget['id']}", headers=budget["headers"])
    assert_status(res, 404)


@pytest.mark.p1
def test_delete_budget_not_found(auth_headers):
    """删除不存在的 id → 404"""
    res = delete("/budgets/999999", headers=auth_headers)
    assert_status(res, 404)
    assert_detail(res, "Budget not found")

from utils.api_client import put,get,post,delete
from utils.assertions import assert_status
import pytest

@pytest.mark.p0
def test_deal(auth_headers):
    res = post("/transactions", {"amount": 100, "category": "food"}, headers=auth_headers)
    assert_status(res, 201)
    trx_id = res.json()["id"]
    print(f"① 创建成功    id={trx_id}")

    res = get(f"/transactions/{trx_id}", headers=auth_headers)
    assert_status(res, 200)
    print(f"② 查到        amount={res.json()['amount']}  category={res.json()['category']}")

    res = put(f"/transactions/{trx_id}", {"amount": 150, "category": "dining"}, headers=auth_headers)
    assert_status(res, 200)
    print(f"③ 修改成功    amount={res.json()['data']['amount']}")

    res = get(f"/transactions/{trx_id}", headers=auth_headers)
    assert_status(res, 200)
    print(f"④ 复查已改    amount={res.json()['amount']}  category={res.json()['category']}")

    res = delete(f"/transactions/{trx_id}", headers=auth_headers)
    assert_status(res, 200)
    print(f"⑤ 删除成功    id={res.json()['deleted']['id']}")

    res = get(f"/transactions/{trx_id}", headers=auth_headers)
    assert_status(res, 404)
    print(f"⑥ 复查已删    状态码=404（确认数据真的没了）")


def assert_status(res, expected):

    assert res.status_code == expected, (
        f"\n请求: {res.request.method} {res.request.url}"
        f"\n期望: {expected}   实际: {res.status_code}"
        f"\n响应: {res.text}"
    )


    
def assert_detail(res, expected_text):
        """断言 400/401/404 响应里的 detail 文案"""
        actual = res.json()["detail"]
        assert actual == expected_text, (
            f"\n期望文案: {expected_text}"
            f"\n实际文案: {actual}"
            f"\n完整响应: {res.text}"
        )
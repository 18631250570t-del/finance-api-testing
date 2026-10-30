from utils.api_client import get_token

token = get_token("2835365398@qq.com", "12345678")
print("token 前 20 位:", token[:20])
print("长度:", len(token))
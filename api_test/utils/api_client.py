import json
import requests

BASE_URL="http://127.0.0.1:8000"
def get(path,headers=None):
    path=BASE_URL+path
    res=requests.get(path,headers=headers,timeout=10)
    return res


def post(path,body,headers=None):
    path=BASE_URL+path
    res=requests.post(path,json=body,headers=headers,timeout=10)
    return res
def get_token(email,password):
    res=post("/login",{"email":email,"password":password})
    return res.json()["access_token"]

def put(path, body, headers=None):
    path=BASE_URL+path
    res = requests.put(path, json=body, headers=headers, timeout=10)
    return res

def delete(path, headers=None):
    path = BASE_URL + path
    res = requests.delete(path, headers=headers, timeout=10)
    return res
def call(method, path, body=None, headers=None):
    """通用请求：method 传 'GET'/'POST'/'PUT'/'DELETE'"""
    return requests.request(method, BASE_URL + path, json=body,
                            headers=headers, timeout=10)
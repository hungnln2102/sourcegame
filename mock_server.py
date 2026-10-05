from flask import Flask, jsonify, request
import json

app = Flask(__name__)

# Mock Server List Data matching Cocos ServerListInfo schema
SERVER_LIST = [
    {
        "server_id": 1001,
        "name": "S1 - Chiến Trận Việt Nam (Mock Server)",
        "ip": "127.0.0.1",
        "port": 8088,
        "flag": 1,  # 1: New Server
        "is_suggest": True
    }
]

# Mock User Profile Data
MOCK_USER = {
    "uid": "10001",
    "username": "AdminModder",
    "level": 99,
    "vip_level": 10,
    "gold": 9999999,
    "gem": 888888,
    "energy": 999
}

@app.route('/get_server_list', methods=['GET', 'POST'])
def get_server_list():
    return jsonify({
        "code": 0,
        "msg": "Success",
        "data": {
            "servers": SERVER_LIST,
            "last_server": 1001
        }
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    return jsonify({
        "code": 0,
        "msg": "Login successful",
        "data": {
            "token": "mock_token_99999",
            "uid": MOCK_USER["uid"],
            "user_info": MOCK_USER
        }
    })

@app.route('/get_user_info', methods=['GET', 'POST'])
def get_user_info():
    return jsonify({
        "code": 0,
        "msg": "Success",
        "data": MOCK_USER
    })

if __name__ == '__main__':
    print("==================================================")
    print("   Last Green: Tower Defense - Mock Server Engine")
    print("==================================================")
    print("Running HTTP Server at http://127.0.0.1:5000")
    print("Endpoints provided:")
    print(" - /get_server_list (Server List query)")
    print(" - /login (Authentication mock)")
    print(" - /get_user_info (User stats mock)")
    print("==================================================")
    app.run(host='0.0.0.0', port=5000)

from http.server import BaseHTTPRequestHandler
import json
import datetime


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. 设置响应头，允许跨域（方便本地调试）
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # 2. 模拟一个简单的排盘结果
        # 这里以后会替换成你的真实排盘算法
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "message": "Python 后端连接成功！",
            "time": current_time,
            "gua_name": "天火同人",
            "result": "上上卦"
        }

        # 3. 返回 JSON 数据
        self.wfile.write(json.dumps(data).encode('utf-8'))
        return
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, gzip, interfaces_pb2

def build(n=10000):
    return [{
        "name": f"eth{i}",
        "description": f"Interface {i}",
        "admin_up": True,
        "oper_up": (i % 10 != 0),
        "mtu": 1500,
        "mac_address": f"00:11:22:33:{(i // 256) % 256:02x}:{i % 256:02x}",
        "ipv4_address": f"192.168.{(i // 256) % 256}.{i % 256}",
        "speed_mbps": 1000 if i % 5 else 10000,
        "in_octets": i * 100000,
        "out_octets": i * 120000,
        "in_errors": i % 7,
        "out_errors": i % 11
    } for i in range(1,n+1)]

DATA = build()

def json_data():
    return json.dumps({"interfaces": DATA}, separators=(",",":")).encode()

def pb_data():
    c = interfaces_pb2.InterfaceCollection()
    for i in DATA:
        m=c.interfaces.add()
        m.name=i["name"]
        m.description=i["description"]
        m.admin_up=i["admin_up"]
        m.oper_up=i["oper_up"]
        m.mtu=i["mtu"]
        m.mac_address=i["mac_address"]
        m.ipv4_address=i["ipv4_address"]
        m.speed_mbps=i["speed_mbps"]
        m.in_octets=i["in_octets"]
        m.out_octets=i["out_octets"]
        m.in_errors=i["in_errors"]
        m.out_errors=i["out_errors"]
    return c.SerializeToString()

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/json":
            d=json_data()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",str(len(d)))
            self.end_headers()
            self.wfile.write(d)

        elif self.path=="/json-gzip":
            d=gzip.compress(json_data())
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Content-Encoding","gzip")
            self.send_header("Content-Length",str(len(d)))
            self.end_headers()
            self.wfile.write(d)

        elif self.path=="/protobuf":
            d=pb_data()
            self.send_response(200)
            self.send_header("Content-Type","application/x-protobuf")
            self.send_header("Content-Length",str(len(d)))
            self.end_headers()
            self.wfile.write(d)

        elif self.path=="/protobuf-gzip":
            d=gzip.compress(pb_data())
            self.send_response(200)
            self.send_header("Content-Type","application/x-protobuf")
            self.send_header("Content-Encoding","gzip")
            self.send_header("Content-Length",str(len(d)))
            self.end_headers()
            self.wfile.write(d)

        else:
            self.send_response(404)
            self.end_headers()

print("Server running on http://localhost:8000")
HTTPServer(("0.0.0.0",8000),H).serve_forever()

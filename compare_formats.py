import json
import gzip
import time
from pathlib import Path
import interfaces_pb2

OUTDIR = Path("output")
OUTDIR.mkdir(exist_ok=True)


def build_dataset(n=50000):
    interfaces = []
    for i in range(1, n + 1):
        interfaces.append({
            "name": f"eth{i}",
            "description": f"Uplink interface {i}",
            "admin_up": True,
            "oper_up": (i % 10 != 0),
            "mtu": 1500,
            "mac_address": f"00:11:22:33:{(i // 256) % 256:02x}:{i % 256:02x}",
            "ipv4_address": f"10.{(i // 65536) % 256}.{(i // 256) % 256}.{i % 256}",
            "speed_mbps": 1000 if i % 5 else 10000,
            "in_octets": i * 100000,
            "out_octets": i * 120000,
            "in_errors": i % 7,
            "out_errors": i % 11
        })
    return interfaces


def write_json(data):
    raw = json.dumps({"interfaces": data}, separators=(",", ":")).encode("utf-8")
    (OUTDIR / "interfaces.json").write_bytes(raw)
    (OUTDIR / "interfaces.json.gz").write_bytes(gzip.compress(raw))
    return raw


def write_pb(data):
    collection = interfaces_pb2.InterfaceCollection()

    for iface in data:
        msg = collection.interfaces.add()
        msg.name = iface["name"]
        msg.description = iface["description"]
        msg.admin_up = iface["admin_up"]
        msg.oper_up = iface["oper_up"]
        msg.mtu = iface["mtu"]
        msg.mac_address = iface["mac_address"]
        msg.ipv4_address = iface["ipv4_address"]
        msg.speed_mbps = iface["speed_mbps"]
        msg.in_octets = iface["in_octets"]
        msg.out_octets = iface["out_octets"]
        msg.in_errors = iface["in_errors"]
        msg.out_errors = iface["out_errors"]

    raw = collection.SerializeToString()
    (OUTDIR / "interfaces.pb").write_bytes(raw)
    (OUTDIR / "interfaces.pb.gz").write_bytes(gzip.compress(raw))
    return raw


def bench_json(data, rounds=100):
    start = time.perf_counter()
    for _ in range(rounds):
        json.loads(data)
    end = time.perf_counter()
    return end - start


def bench_pb(data, rounds=100):
    start = time.perf_counter()
    for _ in range(rounds):
        obj = interfaces_pb2.InterfaceCollection()
        obj.ParseFromString(data)
    end = time.perf_counter()
    return end - start


def estimate_json_fieldname_overhead(json_bytes):
    json_str = json_bytes.decode("utf-8")

    field_names = [
        "name",
        "description",
        "admin_up",
        "oper_up",
        "mtu",
        "mac_address",
        "ipv4_address",
        "speed_mbps",
        "in_octets",
        "out_octets",
        "in_errors",
        "out_errors",
    ]

    overhead = 0
    field_counts = {}

    for field in field_names:
        token = f'"{field}"'
        count = json_str.count(token)
        field_counts[field] = count
        overhead += count * len(token)

    return overhead, field_counts


def print_file_sizes():
    print("\n=== FILE SIZES ===")
    for filename in ["interfaces.json", "interfaces.json.gz", "interfaces.pb", "interfaces.pb.gz"]:
        size = (OUTDIR / filename).stat().st_size
        print(f"{filename:20} {size:>12,} bytes")


def main():
    rounds = 100
    dataset_size = 50000

    print(f"Building dataset with {dataset_size:,} interfaces...")
    interfaces = build_dataset(dataset_size)

    print("Writing JSON and Protobuf files...")
    json_bytes = write_json(interfaces)
    pb_bytes = write_pb(interfaces)

    print_file_sizes()

    json_time = bench_json(json_bytes, rounds=rounds)
    pb_time = bench_pb(pb_bytes, rounds=rounds)

    json_overhead_bytes, field_counts = estimate_json_fieldname_overhead(json_bytes)

    print(f"\n=== PARSE TIME ({rounds} iterations) ===")
    print(f"JSON:     {json_time:.4f} seconds")
    print(f"Protobuf: {pb_time:.4f} seconds")

    print("\n=== PER PARSE LATENCY ===")
    print(f"JSON:     {json_time / rounds:.6f} sec per parse")
    print(f"Protobuf: {pb_time / rounds:.6f} sec per parse")

    print("\n=== SIZE RATIOS ===")
    print(f"Protobuf / JSON raw size:      {len(pb_bytes) / len(json_bytes):.4f}")
    print(
        f"Protobuf.gz / JSON.gz size:    "
        f"{(OUTDIR / 'interfaces.pb.gz').stat().st_size / (OUTDIR / 'interfaces.json.gz').stat().st_size:.4f}"
    )

    print("\n=== JSON FIELD NAME OVERHEAD ===")
    print(f"Estimated bytes used by field names: {json_overhead_bytes:,}")
    print(f"Percentage of raw JSON:              {100 * json_overhead_bytes / len(json_bytes):.2f}%")

    print("\n=== FIELD REPETITION COUNTS ===")
    for field, count in field_counts.items():
        print(f"{field:15} {count:>10,}")

    print("\nDone. Output files are in ./output/")


if __name__ == "__main__":
    main()

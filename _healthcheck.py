"""Quick health + math bypass verification against live server."""
import urllib.request, json, time

base = "http://localhost:3000"

def post_solve(problem):
    req = urllib.request.Request(
        f"{base}/solve",
        data=json.dumps({"problem": problem}).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    res = json.loads(urllib.request.urlopen(req, timeout=10).read())
    wall = int((time.perf_counter() - t0) * 1000)
    return res["result"]["text"], res["duration_ms"], wall

print("=== Health ===")
h = json.loads(urllib.request.urlopen(f"{base}/health", timeout=5).read())
print("HEALTH:", h)

resp = urllib.request.urlopen(f"{base}/", timeout=5)
print(f"UI page: {resp.status}  ({len(resp.read())} bytes)")

print("\n=== Math bypass (should be <10ms) ===")
for expr, expected in [("12*12", "144"), ("sqrt(144)", "12"), ("2**8", "256"), ("100 / 4", "25")]:
    txt, sms, wms = post_solve(expr)
    ok = "OK" if txt == expected else f"FAIL (expected {expected})"
    print(f"  {expr:<15} -> {txt!r:<10} server={sms}ms wall={wms}ms  {ok}")

print("\n=== Recent runs ===")
runs = json.loads(urllib.request.urlopen(f"{base}/runs", timeout=5).read())
print(f"  Total logged: {len(runs['runs'])}")
for r in runs["runs"][:5]:
    print(f"  [{r['status']:<9}] {r['problem']:<20} -> {r['result_preview']!r:<10} ({r['duration_ms']}ms)")

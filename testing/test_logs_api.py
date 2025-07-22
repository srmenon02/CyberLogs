import asyncio
import httpx

BASE_URL = "http://localhost:8000/logs"
TIMEOUT  = 20.0

async def fetch(params, expect_status=200):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(BASE_URL, params=params)
        assert r.status_code == expect_status, f"{params} → {r.status_code} {r.text}"
        return r.json() if expect_status == 200 else r.text

# ── Positive tests ───────────────────────────────────────────────────────────
async def test_page_1_page_size_5():
    data = await fetch({"page": 1, "page_size": 5})
    print("✅ page 1 size 5:", len(data["logs"]), "logs returned")

async def test_sort_asc():
    data = await fetch({"page": 1, "page_size": 3, "sort_by": "timestamp", "sort_order": "asc"})
    ts = [log["timestamp"] for log in data["logs"]]
    assert ts == sorted(ts), "Timestamps not ascending"
    print("✅ sort asc ok:", ts)

async def test_sort_desc():
    data = await fetch({"page": 1, "page_size": 3, "sort_by": "timestamp", "sort_order": "desc"})
    ts = [log["timestamp"] for log in data["logs"]]
    assert ts == sorted(ts, reverse=True), "Timestamps not descending"
    print("✅ sort desc ok:", ts)

async def test_filter_event_keyword():
    data = await fetch({"event_keyword": "disk"})
    assert all("disk" in log["event"].lower() for log in data["logs"]), "Not all logs contain 'disk'"
    print("✅ event_keyword filter ok")

async def test_filter_host():
    data = await fetch({"host": "server-1"})
    assert all(log["host"] == "server-1" for log in data["logs"]), "Not all logs are from 'server-1'"
    print("✅ host filter ok")

# ── Negative / validation tests ──────────────────────────────────────────────
async def test_invalid_page_size():
    await fetch({"page_size": 101}, expect_status=422)
    print("✅ invalid page_size (101) rejected")

async def test_invalid_start_time():
    await fetch({"start_time": "not-a-date"}, expect_status=422)
    print("✅ invalid start_time rejected")

# ── Runner ────────────────────────────────────────────────────────────────────
async def main():
    await test_page_1_page_size_5()
    await test_sort_asc()
    await test_sort_desc()
    await test_filter_event_keyword()
    await test_filter_host()
    await test_invalid_page_size()
    await test_invalid_start_time()

if __name__ == "__main__":
    asyncio.run(main())

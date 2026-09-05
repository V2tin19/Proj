"""Load test for /api/generate-resume endpoint.

Usage:
    cd backend
    python tests/load_test_generate.py

Requirements:
    pip install httpx
"""

from __future__ import annotations

import asyncio
import statistics
import sys
import time
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "http://127.0.0.1:8000"
CONCURRENCY = 20
REQUEST_TIMEOUT = 65.0  # slightly above 60s to catch slow responses

# A minimal valid payload that triggers local fallback (no LLM key needed)
# If you want to test with real LLM, fill in a working api_url/api_key in the payload
# or set LLM_API_URL / LLM_API_KEY env vars before starting the backend.
DEFAULT_PAYLOAD = {
    "name": "压测用户",
    "gender": "男",
    "age": "22",
    "phone": "13800138000",
    "email": "test@example.com",
    "website": "",
    "school": "测试大学",
    "major": "计算机科学与技术",
    "degree": "本科",
    "politicalStatus": "",
    "applicationPosition": "前端开发工程师",
    "targetRole": "前端开发",
    "targetIndustry": "互联网",
    "ranking": "",
    "courses": "数据结构;操作系统;计算机网络",
    "skillsText": "Vue\nReact\nTypeScript",
    "honorsText": "优秀毕业生\n国家奖学金",
    "interests": "",
    "selfIntroduction": "热爱前端开发，具备扎实的技术基础和项目经验。",
    "templateId": "",
    "enableRag": False,
    "wordCount": 800,
    "educationExperiences": [
        {"school": "测试大学", "degree": "本科", "major": "计算机科学与技术", "startDate": "2020-09", "endDate": "2024-06"}
    ],
    "workExperiences": [],
    "projectExperiences": [
        {"projectName": "测试项目", "role": "前端开发", "startDate": "2023-03", "endDate": "2023-06", "briefIntroduction": "一个测试项目", "description": "负责前端页面开发；使用 Vue 3 + TypeScript"}
    ],
}


# ---------------------------------------------------------------------------
# Request logic
# ---------------------------------------------------------------------------

async def send_one(client: httpx.AsyncClient, payload: dict, seq: int) -> dict:
    start = time.perf_counter()
    try:
        response = await client.post(
            f"{BASE_URL}/api/generate-resume",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        elapsed = time.perf_counter() - start
        if response.status_code == 200:
            data = response.json()
            provider = data.get("meta", {}).get("provider", "unknown")
            return {
                "seq": seq,
                "status": "success",
                "elapsed": elapsed,
                "provider": provider,
                "error": None,
            }
        else:
            return {
                "seq": seq,
                "status": "error",
                "elapsed": elapsed,
                "provider": None,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
            }
    except httpx.TimeoutException:
        elapsed = time.perf_counter() - start
        return {
            "seq": seq,
            "status": "timeout",
            "elapsed": elapsed,
            "provider": None,
            "error": f"Request exceeded {REQUEST_TIMEOUT}s",
        }
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return {
            "seq": seq,
            "status": "exception",
            "elapsed": elapsed,
            "provider": None,
            "error": str(exc),
        }


async def run_load_test(concurrency: int = CONCURRENCY) -> None:
    print(f"\n{'=' * 60}")
    print(f"Load Test: {BASE_URL}/api/generate-resume")
    print(f"Concurrency: {concurrency}")
    print(f"{'=' * 60}\n")

    # First, warm up with a single request to ensure backend is reachable
    async with httpx.AsyncClient() as client:
        print("[Warm-up] Sending 1 request...")
        warmup = await send_one(client, DEFAULT_PAYLOAD, 0)
        if warmup["status"] != "success":
            print(f"[Warm-up] FAILED: {warmup['error']}")
            print("Please ensure the backend is running and reachable.")
            sys.exit(1)
        print(f"[Warm-up] OK ({warmup['elapsed']:.2f}s, provider={warmup['provider']})\n")

    # Run concurrent requests
    results: list[dict] = []
    start_all = time.perf_counter()

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_request(seq: int) -> dict:
            async with semaphore:
                return await send_one(client, DEFAULT_PAYLOAD, seq)

        tasks = [bounded_request(i + 1) for i in range(concurrency)]
        results = await asyncio.gather(*tasks)

    total_elapsed = time.perf_counter() - start_all

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    success_results = [r for r in results if r["status"] == "success"]
    error_results = [r for r in results if r["status"] != "success"]
    elapsed_list = [r["elapsed"] for r in success_results]

    print(f"Total time (including concurrency): {total_elapsed:.2f}s")
    print(f"Total requests: {len(results)}")
    print(f"Success: {len(success_results)}")
    print(f"Failed: {len(error_results)}")
    print(f"Failure rate: {len(error_results) / len(results) * 100:.1f}%")

    if elapsed_list:
        print(f"\n--- Response Time (successful requests only) ---")
        print(f"Min:    {min(elapsed_list):.2f}s")
        print(f"Max:    {max(elapsed_list):.2f}s")
        print(f"Mean:   {statistics.mean(elapsed_list):.2f}s")
        if len(elapsed_list) >= 2:
            print(f"P95:    {statistics.quantiles(elapsed_list, n=20)[18]:.2f}s")
        print(f"All < 60s: {'YES' if all(e < 60 for e in elapsed_list) else 'NO'}")

    if error_results:
        print(f"\n--- Errors ---")
        for r in error_results[:5]:
            print(f"  #{r['seq']}: {r['status']} after {r['elapsed']:.2f}s | {r['error']}")
        if len(error_results) > 5:
            print(f"  ... and {len(error_results) - 5} more errors")

    # Provider breakdown
    providers = {}
    for r in success_results:
        p = r.get("provider", "unknown")
        providers[p] = providers.get(p, 0) + 1
    if providers:
        print(f"\n--- Provider Breakdown ---")
        for p, c in providers.items():
            print(f"  {p}: {c}")

    print(f"\n{'=' * 60}")
    if error_results:
        print("RESULT: FAILED (some requests did not succeed)")
        sys.exit(1)
    elif any(e >= 60 for e in elapsed_list):
        print("RESULT: PASSED with WARNING (some requests >= 60s)")
    else:
        print("RESULT: ALL PASSED")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    asyncio.run(run_load_test())

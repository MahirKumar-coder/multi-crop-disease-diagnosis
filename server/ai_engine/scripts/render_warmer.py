import time
import datetime
import requests

TARGET_URL = "https://multi-crop-disease-diagnosis.onrender.com/health"
PING_INTERVAL_SECONDS = 300  # Ping every 5 minutes

def run_warmer():
    print("=" * 70)
    print(" 🚀 RENDER FREE-TIER CONTAINER PRE-WARMER ACTIVE")
    print(f" Target URL : {TARGET_URL}")
    print(f" Interval   : Every {PING_INTERVAL_SECONDS // 60} minutes")
    print("=" * 70)

    consecutive_failures = 0

    while True:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            start_t = time.perf_counter()
            response = requests.get(TARGET_URL, timeout=30)
            latency_ms = (time.perf_counter() - start_t) * 1000

            if response.status_code == 200:
                consecutive_failures = 0
                print(f"[{timestamp}] ✅ Health Ping OK | Status: 200 | Latency: {latency_ms:.2f} ms (Container Warm)")
            else:
                consecutive_failures += 1
                print(f"[{timestamp}] ⚠️ Warning: Unexpected status {response.status_code} | Latency: {latency_ms:.2f} ms")

        except requests.exceptions.Timeout:
            consecutive_failures += 1
            print(f"[{timestamp}] ⏳ Request timed out (Container may be waking up from sleep)...")
        except requests.exceptions.RequestException as e:
            consecutive_failures += 1
            print(f"[{timestamp}] ❌ Connection error: {str(e)}")

        if consecutive_failures >= 3:
            print(f"[{timestamp}] 🚨 CRITICAL: 3 consecutive pings failed. Verify Render service dashboard!")

        time.sleep(PING_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_warmer()
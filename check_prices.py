import os
import requests
from dotenv import load_dotenv

MAX_PRICE = 0.55
SMSPOOL_SERVICE_GOOGLE = 395

load_dotenv()
token = os.environ["SMSPOOL_TOKEN"]

# Step 1: get country list
res = requests.post("https://api.smspool.net/country/retrieve_all", params={"key": token}, timeout=20)
res.raise_for_status()
countries = res.json()
print(f"Got {len(countries)} countries from SMSPool.")

# Step 2: query Google price for each
results = []
for c in countries:
    cid = c.get("ID") or c.get("id")
    name = c.get("name") or c.get("country") or str(cid)
    try:
        r = requests.post(
            "https://api.smspool.net/request/price",
            params={"key": token, "country": cid, "service": SMSPOOL_SERVICE_GOOGLE},
            timeout=15,
        )
        d = r.json()
        price = d.get("price")
        rate = d.get("success_rate")
        if price is None:
            continue
        results.append((float(price), name, cid, rate))
    except Exception as e:
        print(f"  {name} ({cid}): error {e}")

results.sort()
print("\nAll Google prices on SMSPool (sorted cheapest first):")
for price, name, cid, rate in results:
    marker = " <-- under budget" if price <= MAX_PRICE else ""
    print(f"  {name:30s} (id={cid:>4}) ${price:.2f}  success={rate}%{marker}")

cheap = [r for r in results if r[0] <= MAX_PRICE]
print(f"\n{len(cheap)} countries under ${MAX_PRICE:.2f}.")

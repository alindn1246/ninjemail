import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from ninjemail import Ninjemail

MAX_PRICE = 0.55
SMSPOOL_SERVICE_GOOGLE = 395
SMSPOOL_COUNTRY = 8  # Portugal — $0.13, 76% success rate
CSV_PATH = Path(__file__).parent / "gmail_accounts.csv"


def append_to_csv(email: str, password: str, country: int) -> None:
    write_header = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["created_at_utc", "email", "password", "sms_country_id"])
        writer.writerow([
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            email,
            password,
            country,
        ])


def main() -> None:
    load_dotenv()

    token = os.environ["SMSPOOL_TOKEN"]
    proxies = [os.environ[k] for k in ("PROXY_1", "PROXY_2", "PROXY_3", "PROXY_4", "PROXY_5")]

    print(f"Checking SMSPool price for Google (country id={SMSPOOL_COUNTRY}), max budget ${MAX_PRICE:.2f}...")
    res = requests.post(
        "https://api.smspool.net/request/price",
        params={
            "key": token,
            "country": SMSPOOL_COUNTRY,
            "service": SMSPOOL_SERVICE_GOOGLE,
        },
        timeout=20,
    )
    res.raise_for_status()
    info = res.json()
    print(f"SMSPool response: {info}")

    price = float(info.get("price", 0))
    if price <= 0:
        print("Could not parse a price from SMSPool. Aborting.")
        sys.exit(1)
    if price > MAX_PRICE:
        print(f"Price ${price:.2f} exceeds budget ${MAX_PRICE:.2f}. Aborting before any charge.")
        sys.exit(1)

    print(f"Price ${price:.2f} is within budget. Starting Gmail creation...")

    ninja = Ninjemail(
        browser="undetected-chrome",
        sms_keys={"smspool": {"token": token, "country": SMSPOOL_COUNTRY}},
        proxies=proxies,
    )

    email, password = ninja.create_gmail_account(use_proxy=True)

    if email and password:
        append_to_csv(email, password, SMSPOOL_COUNTRY)
        print(f"\nSaved to {CSV_PATH.name}")
        print(f"Email:    {email}")
        print(f"Password: {password}")
    else:
        print("Account creation returned no credentials.")
        sys.exit(1)


if __name__ == "__main__":
    main()

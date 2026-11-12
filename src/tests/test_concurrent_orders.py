
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import HTTPError


URL = "http://127.0.0.1:8000/api/v1/orders"

HEADERS = {
    "Content-Type": "application/json",
    "Idempotency-Key": "concurrent-test-001",
}

PAYLOAD = {
    "user_id": "04e7aa5b-83ee-4468-a79d-d379698a4e0c",
    "items": [
        {
            "product_id": "11111111-1111-4111-8111-111111111111",
            "quantity": 2,
        }
    ],
}


def send_order():
    request = Request(
        URL,
        data=json.dumps(PAYLOAD).encode(),
        headers=HEADERS,
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read())

    except HTTPError as error:
        return error.code, json.loads(error.read())


with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(lambda _: send_order(), range(2)))

for index, (status, body) in enumerate(results, start=1):
    print(f"\nRequest {index}")
    print("Status:", status)
    print("Response:", body)

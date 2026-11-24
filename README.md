# UK vehicle data API for Python

DVLA vehicle enquiry and DVSA MOT history in one call, from a UK registration. Each lookup also gives an estimated ULEZ / clean air zone status, mileage anomaly checks, and MOT and tax expiry countdowns and webhooks. Standard library only, Python 3.9+.

Free key in seconds, with 100 lookups a month: https://api.tychelabs.net/signup. Docs: https://api.tychelabs.net/docs/vehicle

```sh
pip install git+https://github.com/Tyche-Network/uk-vehicle-data-python
```

```python
from uk_vehicle_data import VehicleData

api = VehicleData()  # reads TYCHE_API_KEY
v = api.lookup("AB12 CDE")["data"]

print(v["make"], v["model"], v["colour"])
print("MOT expires", v["mot"]["expiryDate"], v["mot"]["daysUntilExpiry"], "days")
print("ULEZ (estimate):", v["cleanAirZone"]["result"])
for a in v["mileage"]["anomalies"]:
    print(a["type"], a["detail"])
```

A `tl_test_` key returns sandbox data and is not metered. Errors raise `TycheApiError` with `.status` and `.code`.

```python
api.watch("AB12CDE", "https://example.com/hooks/tyche", days_before=[30, 7, 1])

from uk_vehicle_data import verify_webhook
ok = verify_webhook(request.body, request.headers["tyche-signature"], WEBHOOK_SECRET)
```

Contains public sector information licensed under the Open Government Licence v3.0. Not affiliated with or endorsed by the DVLA or DVSA. Clean air zone results are estimates.

MIT licence. Made by [Tyche Labs](https://www.tychelabs.net).

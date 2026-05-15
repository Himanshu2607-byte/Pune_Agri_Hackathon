import pandas as pd
import requests

# Create dummy excel file
df = pd.DataFrame([{"ph": 6.5, "ec": 1.2, "nitrogen": 120, "phosphorus": 30, "potassium": 180}])
df.to_excel("test.xlsx", index=False)

# Send to backend
with open("test.xlsx", "rb") as f:
    response = requests.post("http://127.0.0.1:8001/api/upload", files={"file": ("test.xlsx", f)})

print("Status code:", response.status_code)
print("Response:", response.text)

import urllib.request
import json

BASE = "http://127.0.0.1:8000"

payload = json.dumps({
    "course_id": "CS101",
    "transcript_chunks": [
        {
            "chunk_id": "chunk_c1",
            "speaker": "Faculty",
            "start_time": 0.0,
            "end_time": 45.0,
            "text": "Welcome students. Compiler design is a fundamental computer science subject."
        },
        {
            "chunk_id": "chunk_c2",
            "speaker": "Faculty",
            "start_time": 45.0,
            "end_time": 90.0,
            "text": "A compiler executes the source code directly."
        },
        {
            "chunk_id": "chunk_c3",
            "speaker": "Faculty",
            "start_time": 90.0,
            "end_time": 135.0,
            "text": "In computer science, bubble sort algorithm execution complexity is O(1)."
        },
        {
            "chunk_id": "chunk_c4",
            "speaker": "Faculty",
            "start_time": 135.0,
            "end_time": 180.0,
            "text": "In Python code snippets we print output like print 'Hello World'"
        }
    ]
}).encode()

req = urllib.request.Request(BASE + "/validation/analyze", data=payload, headers={"Content-Type": "application/json"}, method="POST")
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())

print("=== 1. POST /validation/analyze Response ===")
print(json.dumps(data, indent=2))

lecture_id = data["lecture_id"]

print(f"\n=== 2. GET /validation/{lecture_id} ===")
r2 = urllib.request.urlopen(f"{BASE}/validation/{lecture_id}")
results = json.loads(r2.read())
for item in results:
    print(f"Chunk: {item['chunk_id']} | Category: {item['category']} | Status: {item['validation_status']} | Conf: {item['confidence_score']}")
    print(f"  Reason: {item['reason']}")

print(f"\n=== 3. GET /validation/{lecture_id}/summary ===")
r3 = urllib.request.urlopen(f"{BASE}/validation/{lecture_id}/summary")
summary = json.loads(r3.read())
print(json.dumps(summary, indent=2))

print(f"\n=== 4. GET /validation/{lecture_id}/timeline (NEW TIMELINE API) ===")
r4 = urllib.request.urlopen(f"{BASE}/validation/{lecture_id}/timeline")
timeline = json.loads(r4.read())
print(json.dumps(timeline, indent=2))

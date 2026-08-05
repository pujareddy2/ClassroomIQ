import urllib.request
import json

BASE = "http://127.0.0.1:8000"

payload = json.dumps({
    "course_id": "CS101",
    "chunks": [
        {
            "chunk_id": "cov_c1",
            "speaker": "Faculty",
            "start_time": 0.0,
            "end_time": 280.0,
            "text": "Welcome to compiler design. Introduction to compiler definition, language processors, and history."
        },
        {
            "chunk_id": "cov_c2",
            "speaker": "Faculty",
            "start_time": 280.0,
            "end_time": 300.0,
            "text": "Phases of compiler include lexical analysis, syntax analysis, and semantic analysis."
        },
        {
            "chunk_id": "cov_c3",
            "speaker": "Faculty",
            "start_time": 300.0,
            "end_time": 700.0,
            "text": "Lexical analysis produces tokens from regular expressions using finite automata."
        }
    ]
}).encode()

print("=== 1. POST /coverage/analyze ===")
req = urllib.request.Request(BASE + "/coverage/analyze", data=payload, headers={"Content-Type": "application/json"}, method="POST")
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
print(json.dumps(data, indent=2))
lecture_id = data["lecture_id"]

print(f"\n=== 2. GET /coverage/{lecture_id} ===")
r1 = urllib.request.urlopen(f"{BASE}/coverage/{lecture_id}")
print(json.dumps(json.loads(r1.read()), indent=2))

print(f"\n=== 3. GET /coverage/{lecture_id}/topics ===")
r2 = urllib.request.urlopen(f"{BASE}/coverage/{lecture_id}/topics")
topics = json.loads(r2.read())
for t in topics:
    print(f"Topic: {t['topic_name']} | Status: {t['coverage_status']} | Cov: {t['coverage_percentage']}% | Act: {t['actual_duration_seconds']}s | SeqStatus: {t['sequence_integrity_status']}")

print(f"\n=== 4. GET /coverage/{lecture_id}/remaining ===")
r3 = urllib.request.urlopen(f"{BASE}/coverage/{lecture_id}/remaining")
rem = json.loads(r3.read())
print(f"Remaining Topics Count: {len(rem['remaining_topics'])}")
for r in rem['remaining_topics'][:3]:
    print(f"  Uncovered: {r['topic_name']} (Status: {r['status']})")

print(f"\n=== 5. GET /coverage/{lecture_id}/timeline ===")
r4 = urllib.request.urlopen(f"{BASE}/coverage/{lecture_id}/timeline")
timeline = json.loads(r4.read())
print(json.dumps(timeline, indent=2))

print("\n=== 6. Re-running POST /coverage/analyze for same lecture (Idempotency Test) ===")
payload2 = json.dumps({
    "lecture_id": lecture_id,
    "course_id": "CS101",
    "chunks": [
        {
            "chunk_id": "cov_c1",
            "speaker": "Faculty",
            "start_time": 0.0,
            "end_time": 300.0,
            "text": "Updated analysis: Introduction to compiler definition and history."
        }
    ]
}).encode()
req2 = urllib.request.Request(BASE + "/coverage/analyze", data=payload2, headers={"Content-Type": "application/json"}, method="POST")
resp2 = urllib.request.urlopen(req2)
data2 = json.loads(resp2.read())
print("Re-analysis response:", json.dumps(data2, indent=2))

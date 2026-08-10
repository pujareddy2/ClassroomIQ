from pathlib import Path
from urllib import request
from urllib.error import HTTPError

sample = Path('tmp_test_upload.txt')
sample.write_text('UNIT-I\n\nIntroduction to AI\n\nLearning Outcomes\n', encoding='utf-8')
boundary = '----ClassroomIQBoundary'
body = []
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="title"\r\n\r\n')
body.append(b'Test Upload\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="course_name"\r\n\r\n')
body.append(b'Intro to Testing\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="academic_year"\r\n\r\n')
body.append(b'2026-2027\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="semester"\r\n\r\n')
body.append(b'Fall\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="faculty_name"\r\n\r\n')
body.append(b'Pavan Kumar\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="document_type"\r\n\r\n')
body.append(b'SYLLABUS\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="description"\r\n\r\n')
body.append(b'Test extraction\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="file"; filename="tmp_test_upload.txt"\r\n')
body.append(b'Content-Type: text/plain\r\n\r\n')
body.append(sample.read_bytes())
body.append(b'\r\n')
body.append(f'--{boundary}--\r\n'.encode())
req = request.Request('http://127.0.0.1:8001/curriculum/upload', data=b''.join(body), headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}, method='POST')
try:
    with request.urlopen(req, timeout=30) as resp:
        print(resp.status)
        print(resp.read().decode('utf-8'))
except HTTPError as exc:
    print(exc.code)
    print(exc.read().decode('utf-8'))
finally:
    sample.unlink(missing_ok=True)

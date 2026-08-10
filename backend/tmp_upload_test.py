from pathlib import Path
from urllib import request, parse
from urllib.error import HTTPError, URLError

sample = Path('tmp_test_upload.txt')
sample.write_text('Hello\nWorld\n', encoding='utf-8')

boundary = '----ClassroomIQTestBoundary'
body = []
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="title"\r\n\r\n')
body.append(b'Test Upload\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="course_code"\r\n\r\n')
body.append(b'CS101\r\n')
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
body.append(b'Content-Disposition: form-data; name="department_name"\r\n\r\n')
body.append(b'Computer Science\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="faculty_name"\r\n\r\n')
body.append(b'Test Faculty\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="document_type"\r\n\r\n')
body.append(b'syllabus\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="description"\r\n\r\n')
body.append(b'Manual test upload\r\n')
body.append(f'--{boundary}\r\n'.encode())
body.append(b'Content-Disposition: form-data; name="file"; filename="tmp_test_upload.txt"\r\n')
body.append(b'Content-Type: text/plain\r\n\r\n')
body.append(sample.read_bytes())
body.append(b'\r\n')
body.append(f'--{boundary}--\r\n'.encode())

req = request.Request(
    'http://127.0.0.1:8000/curriculum/upload',
    data=b''.join(body),
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    method='POST',
)

try:
    with request.urlopen(req, timeout=30) as resp:
        print('STATUS', resp.status)
        print(resp.read().decode('utf-8'))
except HTTPError as exc:
    print('STATUS', exc.code)
    print(exc.read().decode('utf-8'))
except URLError as exc:
    print('ERROR', exc)
finally:
    sample.unlink(missing_ok=True)

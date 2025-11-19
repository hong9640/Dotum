전송방식:POST 
전송 주소: {홈페이지주소}/api/v1/auth/signup


요청데이터 예시:

Headers:
Content-Type: application/json
Body:
{
"username": "user@example.com",
"password": "12345678",
}

응답데이터 예시:
HTTP/1.1 201 Created
Content-Type: application/json

{
  "status": "SUCCESS",
  "data": {
    "user": {
      "id": 7,
      "username": "user@example.com",
    },
    "message": "회원가입이 완료되었습니다."
  }
}


중복이메일일시 응답:
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "status": "FAIL",
  "error": {
    "code": "USERNAME_ALREADY_EXISTS",
    "message": "이미 등록된 이메일입니다."
  }
}

전송방식: GET
전송 주소: {홈페이지주소}/api/v1/auth/email/{email}

입력 예시: GET /api/v1/auth/email?email=user@example.com

출력 기대값:
사용가능

HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "SUCCESS",
  "data": {
    "email": "user@example.com",
    "is_duplicate": false,
    "message": "사용 가능한 이메일입니다."
  }
}

사용 불가능

HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "Duplicate",
  "data": {
    "email": "user@example.com",
    "is_duplicate": true,
    "message": "이미 등록된 이메일입니다."
  }
}
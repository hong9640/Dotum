전송방식:POST 
전송 주소: {홈페이지주소}/api/v1/auth/signup


요청데이터 예시:

Headers:
Content-Type: application/json
Body:
{
"username": "user@example.com",
"password": "12345678",
"name": "홍길동",
"phone_number": "01012345678",
"gender": "MALE"
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
      "name": "홍길동",
      "role": "USER",
      "gender": "MALE",
      "created_at": "2025-10-20T14:30:00Z"
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
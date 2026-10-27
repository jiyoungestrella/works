# 5일차 - 환자 관리 및 진료기록 API 설계

> 참고 문서: 5일차 - 진료기록 사용자 요구사항 정의서 (REQ-PTNT-001 ~ 005, REQ-MDR-001 ~ 003, NFR-PTNT-001, NFR-MDR-001)

## 1. 개요

사내 의료인이 환자 정보와 흉부 X-Ray 이미지를 포함한 진료기록을 등록하고, 로그인한 사내 개발진·의료 실무진·연구진이 이를 조회·수정·삭제할 수 있도록 하는 REST API입니다.

| 항목 | 내용 |
| --- | --- |
| Base URL | `/api/v1` |
| 데이터 형식 | `application/json` (X-Ray 업로드 API만 `multipart/form-data`) |
| 문자 인코딩 | UTF-8 |
| 날짜 형식 | ISO 8601 (`2026-10-27T10:30:00+09:00`) |
| 인증 방식 | `Authorization: Bearer {access_token}` |
| API 문서 | Swagger-UI (`/docs`) |

## 2. API 목록

| 요구사항 ID | 기능 | Method | URI | 권한 |
| --- | --- | --- | --- | --- |
| REQ-PTNT-001 | 환자 정보 등록 | `POST` | `/api/v1/patients` | 의료인 |
| REQ-PTNT-002 | 환자 목록 조회 (검색·필터) | `GET` | `/api/v1/patients` | 로그인 사용자 |
| REQ-PTNT-003 | 환자 정보 상세 조회 | `GET` | `/api/v1/patients/{patient_id}` | 로그인 사용자 |
| REQ-PTNT-004 | 환자 정보 수정 | `PATCH` | `/api/v1/patients/{patient_id}` | 로그인 사용자 |
| REQ-PTNT-005 | 환자 정보 삭제 | `DELETE` | `/api/v1/patients/{patient_id}` | 로그인 사용자 |
| REQ-MDR-001 | 진료기록 등록 | `POST` | `/api/v1/patients/{patient_id}/medical-records` | 의료인 |
| REQ-MDR-002 | 진료기록 목록 조회 | `GET` | `/api/v1/patients/{patient_id}/medical-records` | 로그인 사용자 |
| REQ-MDR-003 | 진료기록 상세 조회 | `GET` | `/api/v1/medical-records/{record_id}` | 로그인 사용자 |
| REQ-MDR-003 | X-Ray 이미지 조회 | `GET` | `/api/v1/medical-records/{record_id}/xray-image` | 로그인 사용자 |

> 진료기록 등록 화면의 "환자 검색"은 별도 API 없이 `GET /api/v1/patients?name={검색어}` 를 재사용합니다.

### 2.1 권한 정의

| 역할 (role) | 설명 | 등록 (환자·진료기록) | 조회 | 수정·삭제 |
| --- | --- | :---: | :---: | :---: |
| `DOCTOR` | 사내 의료인 | O | O | O |
| `MEDICAL_STAFF` | 의료 실무진 | X | O | O |
| `DEVELOPER` | 사내 개발진 | X | O | O |
| `RESEARCHER` | 연구진 | X | O | O |

- 토큰이 없거나 유효하지 않으면 `401 Unauthorized`
- 권한이 없는 역할로 등록 API를 호출하면 `403 Forbidden`

## 3. 데이터 모델

### 3.1 Patient (환자)

| 필드 | 타입 | 제약 조건 | 설명 |
| --- | --- | --- | --- |
| `id` | Integer | PK, Auto Increment | 환자 고유 ID |
| `name` | String(50) | NOT NULL | 이름 |
| `age` | Integer | NOT NULL, 0 ~ 150 | 나이 |
| `gender` | Enum | NOT NULL, `MALE` / `FEMALE` | 성별 |
| `phone` | String(13) | NOT NULL, UNIQUE, `010-XXXX-XXXX` | 연락처 (휴대폰 번호) |
| `created_at` | DateTime | NOT NULL | 생성일시 |
| `updated_at` | DateTime | NOT NULL | 수정일시 |

### 3.2 MedicalRecord (진료기록)

| 필드 | 타입 | 제약 조건 | 설명 |
| --- | --- | --- | --- |
| `id` | Integer | PK, Auto Increment | 진료기록 ID |
| `patient_id` | Integer | FK → Patient.id, `ON DELETE CASCADE` | 환자 고유 ID |
| `chart_number` | String(20) | NOT NULL, UNIQUE | 진료 차트 넘버 |
| `symptoms` | Text | NOT NULL | 진료된 증상 |
| `xray_image_path` | String(255) | NOT NULL | 서버 로컬 저장소 내 흉부 X-Ray 이미지 경로 |
| `created_at` | DateTime | NOT NULL | 생성일시 |

### 3.3 관계

```
Patient (1) ──── (N) MedicalRecord
```

- 환자 삭제 시 해당 환자의 진료기록은 DB에서 `CASCADE` 삭제되고, X-Ray 이미지 파일도 로컬 저장소에서 함께 삭제됩니다.

### 3.4 X-Ray 이미지 저장 규칙

- 저장 위치: 서버가 실행되는 환경의 로컬 저장소 `{MEDIA_ROOT}/xray/{patient_id}/{uuid}.{ext}`
- 파일명은 원본 파일명 대신 UUID로 저장하여 충돌과 경로 조작(Path Traversal)을 방지합니다.
- 허용 확장자 / MIME: `jpg`, `jpeg`, `png` (`image/jpeg`, `image/png`)
- 최대 크기: 10MB

## 4. 공통 응답 형식

### 4.1 에러 응답

```json
{
  "status": 404,
  "code": "PATIENT_NOT_FOUND",
  "message": "해당 환자를 찾을 수 없습니다."
}
```

### 4.2 공통 에러 코드

| HTTP Status | code | 설명 |
| --- | --- | --- |
| 400 | `INVALID_INPUT` | 필수 항목 누락, 형식 오류 |
| 400 | `INVALID_FILE` | 허용되지 않은 이미지 형식 또는 용량 초과 |
| 401 | `UNAUTHORIZED` | 인증 토큰 없음 / 만료 |
| 403 | `FORBIDDEN` | 해당 기능에 대한 권한 없음 |
| 404 | `PATIENT_NOT_FOUND` | 환자가 존재하지 않음 |
| 404 | `MEDICAL_RECORD_NOT_FOUND` | 진료기록이 존재하지 않음 |
| 409 | `DUPLICATE_PHONE` | 이미 등록된 연락처 |
| 409 | `DUPLICATE_CHART_NUMBER` | 이미 등록된 차트 넘버 |
| 500 | `INTERNAL_SERVER_ERROR` | 서버 내부 오류 |

> FastAPI 사용 시 요청 본문 검증 실패는 기본적으로 `422 Unprocessable Entity` 로 응답하며, 이를 그대로 사용해도 무방합니다.

### 4.3 페이지네이션

목록 조회 API는 아래 쿼리 파라미터와 응답 형식을 공통으로 사용합니다.

| 파라미터 | 타입 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `page` | Integer | 1 | 페이지 번호 (1부터 시작) |
| `size` | Integer | 20 | 페이지 크기 (최대 100) |

```json
{
  "total": 42,
  "page": 1,
  "size": 20,
  "items": []
}
```

---

## 5. 환자 관리 API

### 5.1 환자 정보 등록 (REQ-PTNT-001)

```
POST /api/v1/patients
```

- 권한: `DOCTOR`

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | :---: | --- |
| `name` | String | O | 이름 (1 ~ 50자) |
| `age` | Integer | O | 나이 (0 ~ 150) |
| `gender` | String | O | `MALE` / `FEMALE` |
| `phone` | String | O | 휴대폰 번호 (`010-1234-5678`) |

```json
{
  "name": "홍길동",
  "age": 35,
  "gender": "MALE",
  "phone": "010-1234-5678"
}
```

**Response `201 Created`**

```json
{
  "id": 1,
  "name": "홍길동",
  "age": 35,
  "gender": "MALE",
  "phone": "010-1234-5678",
  "created_at": "2026-10-27T10:30:00+09:00",
  "updated_at": "2026-10-27T10:30:00+09:00"
}
```

**Error**: `400 INVALID_INPUT`, `401`, `403`, `409 DUPLICATE_PHONE`

---

### 5.2 환자 목록 조회 (REQ-PTNT-002)

```
GET /api/v1/patients
```

- 권한: 로그인 사용자 전체

**Query Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
| --- | --- | :---: | --- |
| `name` | String | X | 이름 검색 (부분 일치, `LIKE %name%`) |
| `gender` | String | X | 성별 필터 (`MALE` / `FEMALE`) |
| `min_age` | Integer | X | 최소 나이 (이상) |
| `max_age` | Integer | X | 최대 나이 (이하) |
| `page` | Integer | X | 페이지 번호 (기본 1) |
| `size` | Integer | X | 페이지 크기 (기본 20) |

- 정렬: `created_at` 내림차순 (최근 등록 순)
- `min_age > max_age` 이면 `400 INVALID_INPUT`

**Request 예시**

```
GET /api/v1/patients?name=홍&gender=MALE&min_age=20&max_age=40&page=1&size=20
```

**Response `200 OK`**

```json
{
  "total": 1,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": 1,
      "name": "홍길동",
      "age": 35,
      "gender": "MALE",
      "phone": "010-1234-5678",
      "created_at": "2026-10-27T10:30:00+09:00",
      "updated_at": "2026-10-27T10:30:00+09:00"
    }
  ]
}
```

**Error**: `400 INVALID_INPUT`, `401`

---

### 5.3 환자 정보 상세 조회 (REQ-PTNT-003)

```
GET /api/v1/patients/{patient_id}
```

- 권한: 로그인 사용자 전체

**Path Parameters**

| 파라미터 | 타입 | 설명 |
| --- | --- | --- |
| `patient_id` | Integer | 환자 고유 ID |

**Response `200 OK`**

```json
{
  "id": 1,
  "name": "홍길동",
  "gender": "MALE",
  "phone": "010-1234-5678",
  "age": 35
}
```

**Error**: `401`, `404 PATIENT_NOT_FOUND`

---

### 5.4 환자 정보 수정 (REQ-PTNT-004)

```
PATCH /api/v1/patients/{patient_id}
```

- 권한: 로그인 사용자 전체
- 수정 가능한 항목은 **이름, 연락처** 뿐이며, 전달된 필드만 수정합니다. (부분 수정이므로 `PATCH` 사용)
- 그 외 필드(`age`, `gender` 등)가 포함되면 무시하지 않고 `400 INVALID_INPUT` 으로 응답합니다.
- 수정 시 `updated_at` 이 현재 시각으로 갱신됩니다.

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | :---: | --- |
| `name` | String | X | 이름 (1 ~ 50자) |
| `phone` | String | X | 휴대폰 번호 (`010-1234-5678`) |

> 두 필드 중 최소 1개는 포함되어야 합니다.

```json
{
  "phone": "010-9876-5432"
}
```

**Response `200 OK`**

```json
{
  "id": 1,
  "name": "홍길동",
  "age": 35,
  "gender": "MALE",
  "phone": "010-9876-5432",
  "created_at": "2026-10-27T10:30:00+09:00",
  "updated_at": "2026-10-27T11:00:00+09:00"
}
```

**Error**: `400 INVALID_INPUT`, `401`, `404 PATIENT_NOT_FOUND`, `409 DUPLICATE_PHONE`

---

### 5.5 환자 정보 삭제 (REQ-PTNT-005)

```
DELETE /api/v1/patients/{patient_id}
```

- 권한: 로그인 사용자 전체
- 클라이언트는 "관련 데이터가 모두 삭제됩니다" 확인 팝업에서 `확인했습니다` 를 누른 경우에만 호출합니다.
- 삭제 처리 순서
  1. 환자의 진료기록에 연결된 X-Ray 이미지 경로 목록 조회
  2. 트랜잭션 내에서 진료기록 → 환자 순으로 DB 영구 삭제 (Hard Delete)
  3. 커밋 성공 후 로컬 저장소의 X-Ray 이미지 파일 삭제 (`{MEDIA_ROOT}/xray/{patient_id}/` 디렉터리 삭제)

**Response `204 No Content`**

(응답 본문 없음)

**Error**: `401`, `404 PATIENT_NOT_FOUND`

---

## 6. 진료기록 API

### 6.1 진료기록 등록 (REQ-MDR-001)

```
POST /api/v1/patients/{patient_id}/medical-records
Content-Type: multipart/form-data
```

- 권한: `DOCTOR`
- 환자 선택은 `GET /api/v1/patients?name=` 으로 검색한 뒤 선택한 환자의 `id` 를 경로에 사용합니다.
- X-Ray 미리보기는 업로드 전 클라이언트에서 처리합니다. (`URL.createObjectURL` 등)

**Path Parameters**

| 파라미터 | 타입 | 설명 |
| --- | --- | --- |
| `patient_id` | Integer | 환자 고유 ID |

**Form Data**

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | :---: | --- |
| `chart_number` | String | O | 진료 차트 넘버 |
| `symptoms` | String | O | 진료된 증상 |
| `xray_image` | File | O | 흉부 X-Ray 이미지 (jpg / jpeg / png, 최대 10MB) |

**Request 예시 (curl)**

```bash
curl -X POST "http://localhost:8000/api/v1/patients/1/medical-records" \
  -H "Authorization: Bearer {access_token}" \
  -F "chart_number=CH-20261027-001" \
  -F "symptoms=3일 전부터 기침과 발열, 호흡 곤란 증상" \
  -F "xray_image=@chest_xray.png"
```

**Response `201 Created`**

```json
{
  "id": 10,
  "patient_id": 1,
  "chart_number": "CH-20261027-001",
  "symptoms": "3일 전부터 기침과 발열, 호흡 곤란 증상",
  "xray_image_url": "/api/v1/medical-records/10/xray-image",
  "created_at": "2026-10-27T14:00:00+09:00"
}
```

- 처리 순서: 파일 검증 → 로컬 저장소에 저장 → DB 저장. DB 저장 실패 시 저장한 파일을 삭제합니다.

**Error**: `400 INVALID_INPUT`, `400 INVALID_FILE`, `401`, `403`, `404 PATIENT_NOT_FOUND`, `409 DUPLICATE_CHART_NUMBER`

---

### 6.2 진료기록 목록 조회 (REQ-MDR-002)

```
GET /api/v1/patients/{patient_id}/medical-records
```

- 권한: 로그인 사용자 전체
- 정렬: `created_at` 내림차순
- `symptoms` 가 **100자를 초과**하면 앞 100자 + `...` 형태로 생략하여 반환합니다.

**Query Parameters**: `page`, `size` (4.3 참고)

**Response `200 OK`**

```json
{
  "total": 2,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": 11,
      "chart_number": "CH-20261027-002",
      "symptoms": "흉통이 지속되며 ... (생략) ...",
      "created_at": "2026-10-27T15:00:00+09:00"
    },
    {
      "id": 10,
      "chart_number": "CH-20261027-001",
      "symptoms": "3일 전부터 기침과 발열, 호흡 곤란 증상",
      "created_at": "2026-10-27T14:00:00+09:00"
    }
  ]
}
```

**Error**: `401`, `404 PATIENT_NOT_FOUND`

---

### 6.3 진료기록 상세 조회 (REQ-MDR-003)

```
GET /api/v1/medical-records/{record_id}
```

- 권한: 로그인 사용자 전체
- 증상은 생략 없이 전체를 반환합니다.

**Path Parameters**

| 파라미터 | 타입 | 설명 |
| --- | --- | --- |
| `record_id` | Integer | 진료기록 ID |

**Response `200 OK`**

```json
{
  "id": 10,
  "chart_number": "CH-20261027-001",
  "symptoms": "3일 전부터 기침과 발열, 호흡 곤란 증상",
  "xray_image_url": "/api/v1/medical-records/10/xray-image",
  "created_at": "2026-10-27T14:00:00+09:00"
}
```

**Error**: `401`, `404 MEDICAL_RECORD_NOT_FOUND`

---

### 6.4 X-Ray 이미지 조회 (REQ-MDR-003)

```
GET /api/v1/medical-records/{record_id}/xray-image
```

- 권한: 로그인 사용자 전체
- 의료 이미지이므로 정적 파일로 공개하지 않고, 인증을 거친 뒤 파일을 응답합니다.

**Response `200 OK`**

- `Content-Type: image/png` 또는 `image/jpeg`
- 본문: 이미지 바이너리

**Error**: `401`, `404 MEDICAL_RECORD_NOT_FOUND` (기록이 없거나 파일이 존재하지 않는 경우)

---

## 7. 비기능 요구사항 (NFR-PTNT-001, NFR-MDR-001)

모든 API는 **최대 3초 이내**에 로직을 처리하고 응답해야 합니다.

| 대상 | 대응 방안 |
| --- | --- |
| 환자 목록 검색·필터 | `patients.name`, `patients.gender`, `patients.age` 인덱스 생성, 페이지네이션 필수 적용 (`size` 최대 100) |
| 진료기록 목록 | `medical_records.patient_id`, `created_at` 인덱스 생성, 목록에서는 이미지 데이터 미포함 |
| X-Ray 업로드 | 파일 크기 10MB 제한, 비동기 파일 쓰기 |
| 환자 삭제 | DB `CASCADE` 로 일괄 삭제, 파일 삭제는 커밋 이후 수행 |
| 모니터링 | 요청 처리 시간을 로깅하여 3초 초과 요청 확인 |

## 8. Swagger-UI 테스트 시나리오

| 순서 | API | 기대 결과 |
| --- | --- | --- |
| 1 | `POST /api/v1/patients` | `201`, 환자 `id` 발급 |
| 2 | `GET /api/v1/patients?name=홍&gender=MALE&min_age=20&max_age=40` | `200`, 등록한 환자가 목록에 포함 |
| 3 | `GET /api/v1/patients/{patient_id}` | `200`, 이름·성별·연락처·나이 반환 |
| 4 | `PATCH /api/v1/patients/{patient_id}` | `200`, 이름/연락처 변경 및 `updated_at` 갱신 |
| 5 | `POST /api/v1/patients/{patient_id}/medical-records` | `201`, X-Ray 이미지 업로드 및 기록 생성 |
| 6 | `GET /api/v1/patients/{patient_id}/medical-records` | `200`, 100자 초과 증상은 `...` 처리 |
| 7 | `GET /api/v1/medical-records/{record_id}` | `200`, 전체 증상과 이미지 URL 반환 |
| 8 | `GET /api/v1/medical-records/{record_id}/xray-image` | `200`, 이미지 표시 |
| 9 | `DELETE /api/v1/patients/{patient_id}` | `204`, 이후 3·6·7·8번 호출 시 `404`, 이미지 파일 삭제 확인 |

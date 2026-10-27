# 5일차 환자 관리 및 진료기록 API 설계

| 항목 | 내용 |
|---|---|
| 문서 목적 | 환자·진료기록 요구사항을 분석하고, 구현 전에 API 명세와 설계 결정을 확정한다 |
| 근거 자료 | 5일차 진료기록 사용자 요구사항 정의서, 프론트엔드 코드(`static/apis.js`, `static/pages.js`), 현재 모델(`app/models/`) |
| 대상 요구사항 | REQ-PTNT-001~005, REQ-MDR-001~003, NFR-PTNT-001, NFR-MDR-001 |
| 선행 작업 | 4일차 User API (JWT 인증, `get_current_user`) |
| 설계 원칙 | ① 기존 화면·DB·권한 체계와 호환 ② 환자 의료 데이터는 인증된 사용자만 접근 ③ 요구사항 추적 가능 |

## 목차
1. [요구사항 분석](#1-요구사항-분석)
2. [공통 규칙](#2-공통-규칙)
3. [API 목록과 요구사항 추적](#3-api-목록과-요구사항-추적)
4. [환자 API 상세](#4-환자-api-상세)
5. [진료기록 API 상세](#5-진료기록-api-상세)
6. [주요 처리 흐름](#6-주요-처리-흐름)
7. [보안 설계](#7-보안-설계)
8. [성능 설계](#8-성능-설계)
9. [설계 결정 기록](#9-설계-결정-기록)
10. [현재 코드에서 변경할 사항](#10-현재-코드에서-변경할-사항)
11. [구현 구조](#11-구현-구조)
12. [테스트 시나리오](#12-테스트-시나리오)
13. [팀 결정이 필요한 사항](#13-팀-결정이-필요한-사항)

---

## 1. 요구사항 분석

### 1-1. 요구사항 요약

| ID | 기능 | 행위자 | 입력 | 출력 | 특이사항 |
|---|---|---|---|---|---|
| REQ-PTNT-001 | 환자 등록 | **의료인** | 이름, 나이, 성별, 연락처 | 등록된 환자 | 모달 입력 |
| REQ-PTNT-002 | 환자 목록 | 개발·의료·연구진 | 이름 검색, 성별·나이 범위 필터 | ID, 이름, 나이, 성별, 연락처, 생성·수정일시 | 검색 + 필터 조합 |
| REQ-PTNT-003 | 환자 상세 | 개발·의료·연구진 | 환자 ID | 이름, 성별, 연락처, 나이 | |
| REQ-PTNT-004 | 환자 수정 | 개발·의료·연구진 | 이름, 연락처 | 수정된 환자 | 두 항목만 수정 가능 |
| REQ-PTNT-005 | 환자 삭제 | 개발·의료·연구진 | 환자 ID | 없음 | **진료기록·X-Ray까지 영구 삭제** |
| REQ-MDR-001 | 진료기록 등록 | **의료인** | 환자 ID, 차트 넘버, 증상, X-Ray 이미지 | 등록된 기록 | **파일 업로드**, 로컬 저장 |
| REQ-MDR-002 | 진료기록 목록 | 개발·의료·연구진 | 환자 ID | 기록 ID, 차트 넘버, 증상, 생성일시 | 증상 100자 초과 시 생략 |
| REQ-MDR-003 | 진료기록 상세 | 개발·의료·연구진 | 기록 ID | 기록 ID, 차트 넘버, 증상, X-Ray 이미지, 생성일시 | |
| NFR-PTNT-001 / NFR-MDR-001 | 성능 | - | - | - | 모든 API 3초 이내 |

### 1-2. 행위자와 권한 분석

요구사항은 행위자를 두 가지로 구분해서 쓰고 있다.

| 요구사항 표현 | 등장 위치 | 해석 |
|---|---|---|
| "사내 **의료인** 역할을 가진 유저" | 환자 등록, 진료기록 등록 (**생성**) | 의료 부서 소속 직원 |
| "로그인 된 사내 **개발진, 의료 실무진, 연구진**" | 조회·수정·삭제 | 부서와 무관한 내부 직원 |

4일차에 정의한 사용자 속성과 연결하면 다음과 같다.

| 사용자 속성 | 값 | 4일차 정의 |
|---|---|---|
| `role` | `pending` / `staff` / `admin` | 대기자는 마이페이지 외 접근 불가, 스태프는 X-Ray 관련 읽기·쓰기·수정, 어드민은 모든 데이터 접근 |
| `department` | `research` / `medical` / `development` | 연구 / 의료 / 개발 |

**→ 권한 기준**

| 권한 이름 | 조건 | 적용 API |
|---|---|---|
| 스태프 이상 | `role ∈ {staff, admin}` | 조회·수정·삭제, X-Ray 이미지 조회 |
| 의료진 | `role == admin` 또는 (`role == staff` **그리고** `department == medical`) | 환자 등록, 진료기록 등록·수정·삭제 |

### 1-3. 데이터 모델 분석

```text
patients 1 ──< N medical_records 1 ──< N xray_images N >── 1 users (업로더)
                       │
                       └──< N ai_analysis_results
```

| 요구사항 | 필요한 데이터 | 현재 모델 | 차이 |
|---|---|---|---|
| 환자 연락처 | `phone_number` | `patients.phone` | **컬럼명 불일치** (화면·`users` 테이블은 `phone_number`) |
| 환자 성별 필수 | NOT NULL | `patients.gender` nullable | **필수 제약 없음** |
| 진료기록 + 이미지 | 기록 1건에 이미지 1장 | `medical_records` 1 : N `xray_images` | 이미 X-Ray 전용 테이블이 있음 → 진료기록에 이미지 컬럼을 새로 만들지 않고 **`xray_images`에 저장**. 테이블은 1:N이지만 **API는 기록당 1장으로 운영**한다 (D15) |
| AI 판독 결과 | 이미지 판독 결과 | `ai_analysis_results`가 `medical_records`에 연결 (이미지 행과는 직접 연결 없음) | 이미지를 교체해도 AI 결과가 자동으로 지워지지 않음 → 교체 시 서비스에서 삭제 (5-5절) |
| 이미지 촬영 일시 | 화면 입력 없음 | `xray_images.shooting_datetime` NOT NULL | **입력값 없음** → 값 결정 필요 |
| 환자 삭제 시 연쇄 삭제 | 진료기록·X-Ray·AI 결과 | 외래키에 삭제 정책 없음 | **삭제가 DB에서 거부됨** |
| 이미지 저장 위치 | 서버 로컬 저장소 | `main.py`가 `media/`를 `/media`로 **공개 서빙** | `media/`에 두면 **로그인 없이 URL로 접근 가능** |

### 1-4. 프론트엔드 계약 분석

저장소에는 이미 화면 코드가 있으므로, API는 화면이 호출하는 형식을 따라야 한다.

| 화면 동작 | 호출 | 전송 형식 | 화면이 사용하는 응답 필드 |
|---|---|---|---|
| 환자 등록 | `POST /patients` | JSON `{name, age, gender, phone_number}` | - |
| 환자 목록 | `GET /patients?name=&gender=&min_age=&max_age=` | 쿼리 | **배열**의 `id, name, age, gender, phone_number` |
| 환자 상세 | `GET /patients/{id}` | - | `name, gender, age, phone_number` |
| 환자 수정 | `PATCH /patients/{id}` | JSON `{name, phone_number}` | - |
| 환자 삭제 | `DELETE /patients/{id}` | - | - |
| 진료기록 등록 | `POST /medical-records` | **`FormData`** `{patient_id, chart_number, symptoms, xray_image}` | - |
| 진료기록 목록 | `GET /patients/{id}/medical-records` | - | **배열**의 `id, chart_number, symptoms, created_at` |
| 진료기록 상세 | `GET /medical-records/{id}` | - | `id, chart_number, symptoms, created_at, xray_image_url, patient_id` |

- 화면은 전화번호에서 하이픈을 제거한 숫자만 보낸다 (`replace(/[^\d]/g, '')`).
- 목록 화면은 응답을 **배열**로 받아 `length`, `map`을 쓴다 → 목록 응답은 배열로 유지한다.
- 목록 화면은 `symptoms`를 받은 그대로 표시한다 → **100자 생략은 서버가 처리**한다.
- 오류는 `error.detail`을 읽어 표시한다 → 오류 형식은 `{"detail": ...}`로 유지한다.
- 상세 화면은 `<img src="xray_image_url">`로 이미지를 표시한다 → 이미지를 인증 API로 바꾸면 **화면 수정이 필요**하다 (7-2절).

---

## 2. 공통 규칙

### 2-1. 기본 규칙

| 항목 | 규칙 |
|---|---|
| 기본 경로 | `/api/v1` |
| 인증 | 모든 API에 `Authorization: Bearer <access_token>` 필요 |
| 요청 형식 | JSON. 진료기록 등록·수정만 `multipart/form-data` |
| 성공 응답 | 단일 자원은 객체, 목록은 배열. `204`는 본문 없음 |
| 오류 응답 | 업무 오류는 `{"detail": "메시지"}`, 입력 검증 오류는 FastAPI 기본 형식 |
| 시간 형식 | ISO 8601, 서버 시간대 **KST(Asia/Seoul)** 기준 (예: `2026-10-27T15:00:00`) |
| 성능 | 모든 API 3초 이내 응답 (8절) |

### 2-2. 권한 의존성 (`core/dependencies.py`에 추가)

| 의존성 | 통과 조건 | 실패 |
|---|---|---|
| `StaffUser` | `role ∈ {staff, admin}` | `403 접근 권한이 없습니다.` |
| `MedicalStaffUser` | `role == admin` 또는 (`role == staff` 그리고 `department == medical`) | `403 의료진만 등록할 수 있습니다.` |

### 2-3. 입력값 검증 규칙

| 항목 | 규칙 | 근거 |
|---|---|---|
| 환자 이름 | 앞뒤 공백 제거 후 1~30자 | `patients.name` `String(30)` |
| 나이 | 0 이상 150 이하 정수 | `SmallInteger`, 현실적 범위 |
| 성별 | `male` / `female` | 4일차 `Gender` Enum |
| 연락처 | `010`으로 시작하는 숫자 11자리 | 4일차 회원 연락처 규칙과 통일 |
| 차트 넘버 | 앞뒤 공백 제거 후 1~50자, 중복 불가 | `chart_number` `String(50)`, UNIQUE |
| 증상 | 앞뒤 공백 제거 후 1자 이상 | `symptoms` `Text` |
| X-Ray 이미지 | JPG·PNG, 10MB 이하, **파일 내용으로 형식 확인** | 7-3절 |

### 2-4. 공통 응답 스키마

**`PatientResponse`**

| 필드 | 타입 | 설명 |
|---|---|---|
| id | integer | 환자 고유 ID |
| name | string | 이름 |
| age | integer | 나이 |
| gender | string | `male`, `female` |
| phone_number | string | 하이픈 없는 연락처 |
| created_at | datetime | 생성일시 |
| updated_at | datetime \| null | 수정일시 |

**`MedicalRecordListItem`** (목록)

| 필드 | 타입 | 설명 |
|---|---|---|
| id | integer | 진료기록 ID |
| chart_number | string | 차트 넘버 |
| symptoms | string | 100자 초과 시 앞 100자 + `...` |
| created_at | datetime | 생성일시 |

**`MedicalRecordResponse`** (등록·상세·수정)

| 필드 | 타입 | 설명 |
|---|---|---|
| id | integer | 진료기록 ID |
| patient_id | integer | 환자 ID |
| chart_number | string | 차트 넘버 |
| symptoms | string | 증상 전체 |
| xray_image_url | string | **이미지 조회 API 경로** `/api/v1/medical-records/{id}/xray-image` (파일 위치를 노출하지 않음) |
| created_at | datetime | 생성일시 |
| updated_at | datetime \| null | 수정일시 |

### 2-5. 오류 코드

| 코드 | 상황 | detail |
|---|---|---|
| 400 | 업무 규칙 위반 | `최소 나이는 최대 나이보다 클 수 없습니다.` / `수정할 항목을 하나 이상 입력하세요.` |
| 401 | 토큰 없음·만료·위조 | `인증 정보가 유효하지 않습니다.` |
| 403 | 권한 부족 | `접근 권한이 없습니다.` / `의료진만 등록할 수 있습니다.` |
| 404 | 대상 없음 | `환자를 찾을 수 없습니다.` / `진료기록을 찾을 수 없습니다.` / `이미지 파일을 찾을 수 없습니다.` |
| 409 | 차트 넘버 중복 | `이미 사용 중인 차트 넘버입니다.` |
| 413 | 파일 용량 초과 | `이미지 용량은 10MB 이하여야 합니다.` |
| 415 | 파일 형식 오류 | `JPG, PNG 이미지만 업로드할 수 있습니다.` |
| 422 | 필수 값 누락, 형식 오류 | FastAPI 검증 오류 |

> `401`은 모든 API에서 공통으로 발생하므로 API별 실패 표에는 생략한다.

---

## 3. API 목록과 요구사항 추적

| No | API | Method | Endpoint | 권한 | 성공 | 요구사항 |
|---|---|---|---|---|---|---|
| 1 | 환자 등록 | POST | `/api/v1/patients` | 의료진 | 201 | REQ-PTNT-001 |
| 2 | 환자 목록 | GET | `/api/v1/patients` | 스태프 이상 | 200 | REQ-PTNT-002 |
| 3 | 환자 상세 | GET | `/api/v1/patients/{patient_id}` | 스태프 이상 | 200 | REQ-PTNT-003 |
| 4 | 환자 수정 | PATCH | `/api/v1/patients/{patient_id}` | 스태프 이상 | 200 | REQ-PTNT-004 |
| 5 | 환자 삭제 | DELETE | `/api/v1/patients/{patient_id}` | 스태프 이상 | 204 | REQ-PTNT-005 |
| 6 | 진료기록 등록 | POST | `/api/v1/medical-records` | 의료진 | 201 | REQ-MDR-001 |
| 7 | 진료기록 목록 | GET | `/api/v1/patients/{patient_id}/medical-records` | 스태프 이상 | 200 | REQ-MDR-002 |
| 8 | 진료기록 상세 | GET | `/api/v1/medical-records/{record_id}` | 스태프 이상 | 200 | REQ-MDR-003 |
| 9 | **X-Ray 이미지 조회** | GET | `/api/v1/medical-records/{record_id}/xray-image` | 스태프 이상 | 200 | REQ-MDR-003 (이미지 표시) |
| 10 | 진료기록 수정 | PATCH | `/api/v1/medical-records/{record_id}` | 의료진 | 200 | 과제 안내문 (추가 설계) |
| 11 | 진료기록 삭제 | DELETE | `/api/v1/medical-records/{record_id}` | 의료진 | 204 | 과제 안내문 (추가 설계) |

- **필수 범위 (1~9)**: 요구사항 정의서 기준. 기능 요구사항 8개를 모두 포함하며, 9번은 REQ-MDR-003의 "흉부 X-Ray 이미지"를 안전하게 보여주기 위한 API다.
- **추가 범위 (10~11)**: 과제 안내문은 "진료기록을 등록, 조회, **수정, 삭제**하는 API"를 요구하지만, 요구사항 정의서와 현재 화면에는 해당 기능이 없다. 팀 논의 결과 **구현하기로 확정**했다 (13절 1번, 담당 팀원 5).
- 성능 요구사항 2개는 모든 API에 공통 적용한다 (8절).

---

## 4. 환자 API 상세

### 4-1. 환자 등록 `POST /api/v1/patients`

| 항목 | 내용 |
|---|---|
| 요구사항 | REQ-PTNT-001 |
| 권한 | 의료진 (`MedicalStaffUser`) |

**Request Body** (`PatientCreateRequest`, 정의되지 않은 필드는 422)

```json
{
  "name": "김환자",
  "age": 45,
  "gender": "female",
  "phone_number": "01098765432"
}
```

**Response `201 Created`**: `PatientResponse`

```json
{
  "id": 1,
  "name": "김환자",
  "age": 45,
  "gender": "female",
  "phone_number": "01098765432",
  "created_at": "2026-10-27T15:00:00",
  "updated_at": null
}
```

| 실패 | 상황 |
|---|---|
| 403 | 의료진이 아님 |
| 422 | 필수 값 누락, 나이 범위·연락처 형식 오류 |

### 4-2. 환자 목록 `GET /api/v1/patients`

| 항목 | 내용 |
|---|---|
| 요구사항 | REQ-PTNT-002 |
| 권한 | 스태프 이상 (`StaffUser`) |

**Query Parameters** (`PatientSearchParams` 모델로 묶어서 받음)

| 이름 | 타입 | 필수 | 조건 |
|---|---|---|---|
| name | string | N | 이름 부분 일치 (`LIKE %name%`). 입력값의 `%`, `_`는 escape해서 일반 문자로 검색 |
| gender | string | N | 일치 |
| min_age | integer | N | `age >= min_age` |
| max_age | integer | N | `age <= max_age` |

- 모든 조건은 AND로 결합한다. 정렬은 `id` 내림차순(최근 등록순).

```http
GET /api/v1/patients?name=김&gender=female&min_age=30&max_age=50
```

**Response `200 OK`**: `PatientResponse` 배열. 결과가 없으면 `[]`.

| 실패 | 상황 |
|---|---|
| 400 | `min_age > max_age` |
| 422 | 잘못된 성별 값, 숫자가 아닌 나이 |

### 4-3. 환자 상세 `GET /api/v1/patients/{patient_id}`

| 항목 | 내용 |
|---|---|
| 요구사항 | REQ-PTNT-003 |
| 권한 | 스태프 이상 |

**Response `200 OK`**: `PatientResponse` / **실패** `404 환자를 찾을 수 없습니다.`

> 정의서의 상세 항목은 이름·성별·연락처·나이지만, 화면이 같은 응답으로 수정 모달을 채우고 진료기록 목록을 부르므로 공통 `PatientResponse`(ID, 생성·수정일시 포함)를 그대로 반환한다.

### 4-4. 환자 수정 `PATCH /api/v1/patients/{patient_id}`

| 항목 | 내용 |
|---|---|
| 요구사항 | REQ-PTNT-004 |
| 권한 | 스태프 이상 |
| 방식 | 부분 수정 (`model_dump(exclude_unset=True)`) |

**Request Body** (`PatientUpdateRequest`, 모두 선택, `extra="forbid"`)

```json
{ "name": "김환자", "phone_number": "01011112222" }
```

**Response `200 OK`**: 수정된 `PatientResponse`

| 실패 | 상황 |
|---|---|
| 400 | 빈 객체 |
| 404 | 환자 없음 |
| 422 | 형식 오류, `age`·`gender` 등 수정 불가 필드 입력 |

### 4-5. 환자 삭제 `DELETE /api/v1/patients/{patient_id}`

| 항목 | 내용 |
|---|---|
| 요구사항 | REQ-PTNT-005 |
| 권한 | 스태프 이상 |

**Response `204 No Content`** / **실패** `404 환자를 찾을 수 없습니다.`

**삭제 범위**

| 대상 | 처리 | 방법 |
|---|---|---|
| `patients` 행 | 삭제 | 직접 삭제 |
| `medical_records` 행 | 삭제 | DB `ON DELETE CASCADE` |
| `xray_images` 행 | 삭제 | DB `ON DELETE CASCADE` |
| `ai_analysis_results` 행 | 삭제 | DB `ON DELETE CASCADE` |
| 환자 이미지 폴더 `storage/xray/{patient_id}/` | 폴더째 삭제 | 서비스에서 커밋 후 삭제 (6-3절) |
| AI 히트맵 파일 | 삭제 | 서비스에서 커밋 후 삭제 |

> DB 외래키의 `ON DELETE CASCADE`만으로는 부족하다. SQLAlchemy 관계에 `passive_deletes=True`가 없으면 ORM이 자식 행을 먼저 불러와 처리하려다 외래키 오류가 날 수 있으므로, 관계에도 함께 지정한다 (10-1절).
>
> 화면의 "관련 데이터가 모두 삭제됩니다" 확인 팝업은 프론트엔드가 처리하고, `확인했습니다`를 누른 경우에만 이 API를 호출한다.

---

## 5. 진료기록 API 상세

### 5-1. 진료기록 등록 `POST /api/v1/medical-records`

| 항목 | 내용 |
|---|---|
| 요구사항 | REQ-MDR-001 |
| 권한 | 의료진 (`MedicalStaffUser`) |
| 형식 | `multipart/form-data` |

**Form 필드**

| 필드 | 타입 | 필수 |
|---|---|---|
| patient_id | integer | Y |
| chart_number | string | Y |
| symptoms | string | Y |
| xray_image | file | Y |

```text
patient_id=1
chart_number=CH-20261027-001
symptoms=기침과 발열이 3일째 지속됨
xray_image=<chest.png>
```

**Response `201 Created`**: `MedicalRecordResponse`

```json
{
  "id": 1,
  "patient_id": 1,
  "chart_number": "CH-20261027-001",
  "symptoms": "기침과 발열이 3일째 지속됨",
  "xray_image_url": "/api/v1/medical-records/1/xray-image",
  "created_at": "2026-10-27T15:30:00",
  "updated_at": null
}
```

| 실패 | 상황 |
|---|---|
| 403 | 의료진이 아님 |
| 404 | 환자 없음 |
| 409 | 차트 넘버 중복 |
| 413 | 10MB 초과 |
| 415 | JPG·PNG가 아님 |
| 422 | 필수 항목 누락 |

- 요구사항의 "환자 정보를 검색하여 환자를 선택"은 별도 API 없이 환자 목록 API(`GET /api/v1/patients?name=`)를 재사용하고, 선택한 환자의 `id`를 `patient_id`로 보낸다.
- 이미지 미리보기는 화면에서 처리한다(`FileReader`). 서버는 저장만 담당한다.
- 저장 위치는 요구사항 비고대로 서버 로컬 저장소이며, **공개 폴더(`media/`)가 아닌 `storage/xray/{patient_id}/{uuid}.{ext}`** 에 저장한다 (7-1절).

### 5-2. 진료기록 목록 `GET /api/v1/patients/{patient_id}/medical-records`

| 항목 | 내용 |
|---|---|
| 요구사항 | REQ-MDR-002 |
| 권한 | 스태프 이상 |

**Response `200 OK`**: `MedicalRecordListItem` 배열, `created_at` 내림차순(최신순)

```json
[
  {
    "id": 1,
    "chart_number": "CH-20261027-001",
    "symptoms": "기침과 발열이 3일째 지속됨",
    "created_at": "2026-10-27T15:30:00"
  }
]
```

| 실패 | 상황 |
|---|---|
| 404 | 환자 없음 (기록이 없는 환자는 `200 []`) |

### 5-3. 진료기록 상세 `GET /api/v1/medical-records/{record_id}`

| 항목 | 내용 |
|---|---|
| 요구사항 | REQ-MDR-003 |
| 권한 | 스태프 이상 |

**Response `200 OK`**: `MedicalRecordResponse` (증상 전체 포함) / **실패** `404 진료기록을 찾을 수 없습니다.`

### 5-4. X-Ray 이미지 조회 `GET /api/v1/medical-records/{record_id}/xray-image`

| 항목 | 내용 |
|---|---|
| 요구사항 | REQ-MDR-003 (상세 화면의 흉부 X-Ray 이미지 표시) |
| 권한 | 스태프 이상 |
| 목적 | 환자 X-Ray를 **인증된 사용자에게만** 제공 (7-2절) |

**Response `200 OK`**
- 본문: 이미지 바이너리 (`FileResponse`)
- 헤더: `Content-Type: image/png` 또는 `image/jpeg`, `Cache-Control: private, no-store`

| 실패 | 상황 |
|---|---|
| 403 | 대기자 |
| 404 | 진료기록 없음, 또는 저장소에 파일이 없음 |

### 5-5. 진료기록 수정 `PATCH /api/v1/medical-records/{record_id}` (추가 설계)

| 항목 | 내용 |
|---|---|
| 근거 | 과제 안내문 (요구사항 정의서·화면에는 없음) |
| 권한 | 의료진 (등록 권한과 동일) |
| 형식 | `multipart/form-data`, 보낸 항목만 수정 |

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| chart_number | string | N | 다른 기록과 중복 불가 |
| symptoms | string | N | |
| xray_image | file | N | 보내면 기존 이미지를 교체 (아래 교체 규칙) |

**이미지 교체 규칙** (진료기록 1건 = 이미지 1장, D15)

1. 새 파일을 저장한다.
2. 기존 이미지 파일 경로와 AI 결과의 `heatmap_url`을 **미리 수집**한다. 행을 삭제한 뒤에는 경로를 알 수 없기 때문이다.
3. 하나의 트랜잭션에서 기존 `xray_images` 행을 삭제하고 새 행을 만든다.
4. 같은 트랜잭션에서 이 진료기록의 `ai_analysis_results`도 삭제한다. AI 결과는 `xray_images`가 아니라 **`medical_records`에 연결**되어 있어서 이미지 행을 지워도 자동으로 지워지지 않는다. 그런데 기존 결과는 **이전 이미지를 판독한 값**이므로 남겨 두면 새 이미지와 맞지 않는다.
5. 커밋 성공 후 2에서 수집한 기존 이미지·히트맵 파일을 삭제한다. 커밋이 실패하면 1에서 저장한 새 파일을 삭제한다. 차트 넘버 `IntegrityError`도 같은 방식으로 롤백 후 409로 응답한다 (D14).

**Response `200 OK`**: 수정된 `MedicalRecordResponse`

| 실패 | 상황 |
|---|---|
| 400 | 수정할 항목 없음 |
| 403 | 의료진이 아님 |
| 404 | 진료기록 없음 |
| 409 | 차트 넘버 중복 |
| 413 / 415 | 이미지 용량·형식 오류 |

### 5-6. 진료기록 삭제 `DELETE /api/v1/medical-records/{record_id}` (추가 설계)

| 항목 | 내용 |
|---|---|
| 근거 | 과제 안내문 |
| 권한 | 의료진 |

**Response `204 No Content`** / **실패** `403`, `404`

- 진료기록 행 삭제 시 `xray_images`, `ai_analysis_results`는 `CASCADE`로 함께 삭제되고, 이미지·히트맵 파일은 커밋 후 삭제한다.
- 처리 순서는 환자 삭제(6-3절)와 같다: **① 기록 존재 확인 → ② 이미지·히트맵 경로 수집 → ③ DB 삭제·커밋 → ④ 파일 삭제**.

---

## 6. 주요 처리 흐름

### 6-1. 진료기록 등록

```text
[화면] FormData 전송
   │
   ▼
[API] MedicalStaffUser 권한 확인 ── 실패 → 403
   │
   ▼
[Service]
   ├─ ① 환자 존재 확인 ─────────── 없음 → 404
   ├─ ② 차트 넘버 중복 사전 확인 ── 중복 → 409  (빠른 실패용)
   ├─ ③ 파일 서명 확인 (앞 몇 바이트) ── 실패 → 415
   ├─ ④ 청크 단위로 읽으며 저장  storage/xray/{patient_id}/{uuid}.{ext}
   │     누적 크기가 10MB를 넘으면 즉시 중단 + 쓰던 파일 삭제 → 413
   ├─ ⑤ DB 저장 (하나의 트랜잭션)
   │     medical_records 1행 + xray_images 1행
   │     uploader_id = 로그인 사용자, shooting_datetime = 업로드 시각
   │
   ├─ 성공 → 201
   ├─ ⑤에서 UNIQUE 위반(IntegrityError) → 롤백 + ④ 파일 삭제 → 409
   └─ ⑤에서 그 밖의 실패 → 롤백 + ④ 파일 삭제 → 500
```

> 파일 저장(④)과 DB 저장(⑤)은 하나의 트랜잭션으로 묶을 수 없다. DB 저장이 실패했을 때 저장된 파일을 지워서 **주인 없는 파일**이 남지 않게 한다.
>
> ②의 사전 확인만으로는 **동시 요청**을 막지 못한다. 두 요청이 동시에 ②를 통과하면 둘 다 INSERT를 시도하므로, 최종 판단은 DB의 UNIQUE 제약에 맡기고 `IntegrityError`를 409로 바꿔 응답한다 (D14).

### 6-2. X-Ray 이미지 표시 (상세 화면)

```text
[화면] GET /medical-records/{id}  ──▶  xray_image_url 받음
   │
   ▼
[화면] fetch(xray_image_url, { headers: { Authorization: Bearer … } })
   │
   ▼
[API] StaffUser 권한 확인 → xray_images.image_url로 파일 위치 조회 → FileResponse
   │
   ▼
[화면] 응답을 Blob으로 변환 → URL.createObjectURL(blob) → <img src>에 연결
```

> `<img src>`는 `Authorization` 헤더를 보낼 수 없으므로, 화면은 `fetch`로 이미지를 받아 Blob URL로 표시한다.

### 6-3. 환자 삭제

```text
[Service]
   ├─ ① 환자 존재 확인 ─────────── 없음 → 404
   ├─ ② 삭제할 파일 경로 수집
   │     storage/xray/{patient_id}/, 환자 진료기록의 heatmap_url
   ├─ ③ DB 삭제 (하나의 트랜잭션)
   │     DELETE patients → CASCADE로 진료기록·X-Ray·AI 결과 자동 삭제
   ├─ ④ 커밋 성공 후 ②의 폴더·파일 삭제 (이미 없으면 무시)
   │     삭제 중 오류가 나도 DB는 이미 삭제되었으므로 로그만 남기고 계속 진행
   └─ 204
```

> 파일을 먼저 지우고 DB 삭제가 실패하면, DB에는 기록이 남았는데 이미지가 없는 상태가 된다. 그래서 **DB 커밋 → 파일 삭제** 순서로 처리한다.

---

## 7. 보안 설계

환자 이름·연락처·증상·흉부 X-Ray는 모두 **민감한 의료 정보**다. 4일차 인증 체계 위에 다음 보안 기준을 적용한다.

### 7-1. 이미지 저장 위치 분리

| 구분 | 위치 | 공개 여부 | 용도 |
|---|---|---|---|
| 공개 정적 파일 | `media/` (`/media`로 서빙) | 누구나 URL로 접근 가능 | 공개해도 되는 파일 |
| **환자 이미지** | **`storage/xray/`** (서빙하지 않음) | 직접 접근 불가 | X-Ray 원본 |

- `storage/`는 웹 경로에 연결하지 않으므로, 파일 위치를 알아도 브라우저로 직접 열 수 없다.
- `storage/`는 `.gitignore`에 추가해 환자 이미지가 Git 저장소에 올라가지 않게 한다.

### 7-2. 이미지 접근 제어

| 위협 | 대응 |
|---|---|
| URL을 알면 로그인 없이 X-Ray 조회 | 이미지는 **인증 API(5-4절)로만** 제공, 대기자는 403 |
| 응답의 파일 경로로 서버 구조 노출 | 응답에는 API 경로만 담고 실제 저장 경로는 숨김 |
| 브라우저·프록시에 의료 이미지 캐시 | `Cache-Control: private, no-store` |

### 7-3. 파일 업로드 검증

| 위협 | 대응 |
|---|---|
| 확장자만 바꾼 악성 파일 (`virus.exe` → `chest.png`) | 확장자·`Content-Type`을 믿지 않고 **파일 앞부분의 서명(매직 넘버)** 으로 형식 확인 (PNG `89 50 4E 47 0D 0A 1A 0A` 8바이트, JPEG `FF D8 FF`). 저장 확장자도 원본 파일명이 아닌 **감지된 형식**으로 정함 |
| 대용량 파일로 서버 저장소 고갈 | FastAPI는 multipart 요청을 받는 시점에 파일을 이미 임시 파일로 받아 두고, `Content-Length` 헤더도 클라이언트가 조작할 수 있다. 그래서 **청크 단위로 읽으며 크기를 누적하고, 10MB를 넘는 순간 중단 후 쓰던 파일을 삭제하고 413**으로 응답한다 |
| 파일명으로 경로 조작 (`../../main.py`) | 원본 파일명은 쓰지 않고 **UUID**로 저장 |
| 같은 이름 파일 덮어쓰기 | UUID로 이름 충돌 방지 |

### 7-4. 권한과 데이터 노출

| 기준 | 내용 |
|---|---|
| 서버에서 권한 확인 | 화면에서 버튼을 숨기는 것과 별개로, 모든 API에서 의존성으로 권한을 확인 |
| 대기자 차단 | 4일차 정의대로 `pending`은 환자·진료기록 API 전부 403 |
| 수정 불가 필드 거부 | 수정 요청에 `extra="forbid"`를 적용해 `age`, `patient_id` 등을 몰래 바꾸지 못하게 함 |

---

## 8. 성능 설계

NFR-PTNT-001, NFR-MDR-001: 모든 API는 3초 이내에 응답한다.

| 대상 | 대응 |
|---|---|
| 환자 이름 검색 | 요구사항이 부분 검색이라 `LIKE '%김%'`처럼 앞에 `%`가 붙어 **B-Tree 인덱스를 타지 않는다.** 현재 환자 수가 적어 전체 조회로도 3초 안에 충분하므로 허용한다. 데이터가 커지면 앞부분 일치(`LIKE '김%'`, 인덱스 사용 가능)나 전문 검색(FULLTEXT)으로 바꾼다 |
| 나이 범위 필터 | `patients.age` 인덱스 (범위 조건 `BETWEEN`에 효과 있음) |
| 진료기록 목록 | `medical_records(patient_id, created_at)` 복합 인덱스 (외래키 인덱스 포함), 목록에는 이미지 데이터를 담지 않음 |
| X-Ray 업로드 | 10MB 제한, 비동기 파일 쓰기 |
| 환자 삭제 | DB `CASCADE`로 한 번에 삭제, 파일 삭제는 커밋 후 처리 |
| 목록 크기 | 현재 화면이 배열을 기대하므로 페이지네이션은 적용하지 않는다. 데이터가 늘어 3초를 넘기면 `page`, `size`를 도입하고 화면을 함께 수정한다 |

---

## 9. 설계 결정 기록

| No | 결정 | 검토한 대안 | 선택 이유 |
|---|---|---|---|
| D1 | 주소·필드명·응답 형식을 **프론트엔드 코드 기준**으로 정함 | 요구사항만 보고 새로 정의 | 화면이 이미 존재하므로, 다르면 API가 동작해도 화면에서 오류가 난다 (4일차 교훈) |
| D2 | 등록 권한을 **"어드민 또는 의료 부서 스태프"** 로 제한 | 스태프 전체 허용 | 요구사항이 등록만 "의료인"으로 구분해 표현했다 |
| D3 | 증상 100자 생략을 **서버**에서 처리 | 화면에서 처리 | 현재 화면은 받은 값을 그대로 표시한다. 목록 응답 크기도 줄어든다 |
| D4 | 연쇄 삭제를 **DB `ON DELETE CASCADE` + ORM `passive_deletes=True`** 로 처리 | 서비스에서 테이블마다 직접 삭제 | 삭제 누락 위험이 없고 코드가 단순하다. ORM이 자식 행을 먼저 건드리지 않게 `passive_deletes`를 함께 건다. 파일은 DB가 지울 수 없어 서비스에서 처리 |
| D5 | 이미지 파일명을 **UUID**로 저장 | 원본 파일명 사용 | 덮어쓰기, 한글·특수문자 경로 문제, 경로 조작 공격을 막는다 |
| D6 | 환자 연락처 **중복 허용** | 회원처럼 UNIQUE | 가족이 같은 번호를 쓰거나 동명이인이 있을 수 있다 |
| D7 | 이미지는 기존 **`xray_images` 테이블**에 저장 | 진료기록에 `xray_image_path` 컬럼 추가 | 3일차에 만든 테이블이 업로더·촬영 일시까지 담고 있고, 같은 진료기록 아래에서 AI 판독 결과와 함께 관리된다 |
| D8 | `shooting_datetime` = **업로드 시각** | nullable로 변경 / 화면에 입력칸 추가 | 화면 변경 없이 필수 제약을 지킬 수 있다. 실제 촬영 일시 입력은 개선 과제 |
| D9 | 목록 조회 파라미터를 **쿼리 모델**로 묶음 | 함수 파라미터로 하나씩 | 조건이 4개라 묶는 편이 읽기 쉽고, `min_age ≤ max_age` 교차 검증을 한곳에서 처리한다 |
| **D10** | X-Ray를 **비공개 저장소 + 인증 API**로 제공 | `media/` 공개 서빙 | URL만 알면 로그인 없이 환자 X-Ray를 볼 수 있다. 상세 화면을 `fetch` + Blob 방식으로 바꾸는 비용을 감수한다 |
| **D11** | 이미지를 **환자별 폴더**에 저장 | 한 폴더에 모두 저장 | 환자 삭제 시 폴더째 지우면 되어 파일 누락이 없다 |
| **D12** | 파일 형식을 **파일 내용(서명)** 으로 검사 | 확장자·`Content-Type`만 검사 | 둘 다 클라이언트가 마음대로 바꿀 수 있는 값이다 |
| **D13** | 목록 응답은 **배열 유지**, 페이지네이션 보류 | `{total, items}` 페이지네이션 | 현재 화면이 배열을 기대한다. 성능 문제가 생기면 화면과 함께 변경한다 |
| **D14** | 차트 넘버 중복은 **DB UNIQUE 제약이 최종 판단**, `IntegrityError` → 409 | 사전 조회만으로 판단 | "조회 후 INSERT"는 동시 요청이 둘 다 통과할 수 있다. 사전 조회는 빠른 실패용으로만 둔다 |
| **D15** | **진료기록 1건 = 이미지 1장**, 교체 시 기존 `xray_images` 행 삭제 + 해당 기록의 AI 결과 삭제 | 기존 행의 경로만 갱신 / 이미지 여러 장 허용 | 요구사항·화면 모두 1장. AI 결과는 이전 이미지를 판독한 값이라 남기면 새 이미지와 맞지 않는다 |
| **D16** | 파일 용량을 **청크 단위로 누적 확인** | `Content-Length` 헤더로 확인 | 헤더는 클라이언트가 조작할 수 있고, FastAPI는 이미 파일을 받아 둔 상태다 |
| **D17** | 이름 검색은 **부분 일치 유지**, 인덱스 효과 없음을 인정 | 앞부분 일치로 변경 | 요구사항은 "이름 기준 검색"이고 화면도 부분 검색을 기대한다. 현재 데이터 규모에서는 3초 요구사항에 문제없다 |

---

## 10. 현재 코드에서 변경할 사항

### 10-1. 백엔드

| 대상 | 현재 | 변경 | 관련 결정 |
|---|---|---|---|
| `patients.phone` | 컬럼명 `phone` | `phone_number`로 변경 | D1 |
| `patients.gender` | `nullable=True` | `nullable=False` | REQ-PTNT-001 |
| `medical_records.patient_id` FK | 삭제 정책 없음 | `ondelete="CASCADE"` | D4 |
| `xray_images.record_id` FK | 삭제 정책 없음 | `ondelete="CASCADE"` | D4 |
| `ai_analysis_results.record_id` FK | 삭제 정책 없음 | `ondelete="CASCADE"` | D4 |
| `Patient.medical_records` 관계 | 옵션 없음 | `passive_deletes=True` | D4 |
| `MedicalRecord.xray_images`, `MedicalRecord.ai_analysis_results` 관계 | 옵션 없음 | `passive_deletes=True` | D4 |
| 인덱스 | 없음 | `patients.age`, `medical_records(patient_id, created_at)` | 8절, D17 |
| `core/dependencies.py` | `CurrentUser`, `AdminUser` | `StaffUser`, `MedicalStaffUser` 추가 | D2 |
| `core/config.py` | - | `XRAY_STORAGE_DIR = "storage/xray"`, `MAX_UPLOAD_SIZE = 10MB` | D10 |
| `.gitignore` | - | `storage/` 추가 | 7-1절 |

- 기존 마이그레이션은 수정하지 않고 **새 리비전**을 추가한다.
- 외래키 삭제 정책 변경은 Alembic이 자동 감지하지 못할 수 있으므로, 생성된 파일에 `drop_constraint` / `create_foreign_key`가 있는지 확인한다.
- **DB별 주의**: 운영 DB는 MySQL(InnoDB)로, 외래키와 `CASCADE`가 기본으로 동작한다. 테스트에서 쓰는 SQLite(`aiosqlite`)는 외래키가 기본으로 꺼져 있어, 연결할 때마다 `PRAGMA foreign_keys=ON`을 실행해야 `CASCADE`가 동작한다.

### 10-2. 프론트엔드

| 대상 | 현재 | 변경 | 관련 결정 |
|---|---|---|---|
| 진료기록 상세 (`pages.js`) | `xray-img.src = record.xray_image_url` | 토큰을 담아 `fetch` → Blob URL로 표시 | D10 |
| `apis.js` | - | `getXrayImage(recordId)` 추가 (Blob 반환) | D10 |

---

## 11. 구현 구조

```text
app/
├── apis/
│   ├── patient_apis.py            # 1~5, 7
│   └── medical_record_apis.py     # 6, 8, 9, (10, 11)
├── schemas/
│   ├── patient.py                 # PatientCreateRequest, PatientUpdateRequest, PatientSearchParams, PatientResponse
│   └── medical_record.py          # MedicalRecordListItem, MedicalRecordResponse
├── services/
│   ├── patient_service.py         # 검색 조건 검증, 삭제 시 폴더 정리
│   └── medical_record_service.py  # 중복 검사, 파일 저장·롤백·교체
├── repositories/
│   ├── patient_repository.py
│   └── medical_record_repository.py
└── core/
    ├── dependencies.py            # StaffUser, MedicalStaffUser
    └── file_storage.py            # 이미지 검사·저장·삭제 공통 함수
```

### 11-1. 담당 배분 (5명)

| 담당 | 공통 기반 (먼저 병합) | API | 설계 문서 | 테스트 |
|---|---|---|---|---|
| 팀원 1 | 모델 수정·마이그레이션 (`phone_number`, 성별 필수, CASCADE 3개 + `passive_deletes`, 인덱스)<br>환자 스키마·저장소 뼈대 (`schemas/patient.py`, `patient_repository.py`) | ① 환자 등록<br>② 환자 목록 | 4-1, 4-2, 8, 10-1 | T1~T6, T22 |
| 팀원 2 | 권한 의존성 (`StaffUser`, `MedicalStaffUser`)<br>파일 저장 함수 (`file_storage.py`: 검사·저장·삭제)<br>진료기록 스키마·저장소 뼈대, 라우터 등록 (`main.py`), `.gitignore` | ⑥ 진료기록 등록 (업로드) | 2-2, 5-1, 6-1, 7-1, 7-3 | T11~T14, T21, T23 |
| 팀원 3 | - | ③ 환자 상세<br>④ 환자 수정<br>⑤ 환자 삭제 (연쇄 삭제 + 폴더 정리) | 4-3~4-5, 6-3 | T7~T10, T25 |
| 팀원 4 | - | ⑦ 진료기록 목록<br>⑧ 진료기록 상세<br>⑨ X-Ray 이미지 조회<br>+ 상세 화면 이미지 표시 (Blob) | 5-2~5-4, 6-2, 7-2, 10-2 | T15~T20 |
| 팀원 5 | - | ⑩ 진료기록 수정 (이미지 교체 포함)<br>⑪ 진료기록 삭제 | 5-5, 5-6 | T24, T26~T28 |

> 스키마·저장소·라우터 파일의 **뼈대는 공통 기반 PR에 포함**한다. 이후에는 각자 자기 함수만 추가하므로 같은 파일을 동시에 고쳐 생기는 충돌이 줄어든다.

### 11-2. 병합 순서

```text
1단계 (먼저 병합)   팀원1 기반 PR,  팀원2 기반 PR
        ↓
2단계 (병렬)        팀원1 ①②  │  팀원2 ⑥  │  팀원3 ③④⑤  │  팀원4 ⑦⑧⑨ + 화면  │  팀원5 ⑩⑪
        ↓
3단계               각자 Swagger-UI에서 Authorize 후 담당 테스트 수행 → main 병합
```

### 11-3. 사전 합의 사항

| 함께 맞출 사람 | 합의할 내용 |
|---|---|
| 팀원 2 ↔ 3, 5 | `file_storage.py`의 함수 이름과 인자 (기반 PR에서 확정) |
| 팀원 2 ↔ 5 | 기록당 이미지 1장 정책(D15), 차트 넘버 `IntegrityError` → 409 처리(D14) |
| 팀원 2 ↔ 4 | `xray_image_url` 형식 (`/api/v1/medical-records/{id}/xray-image`) |
| 팀원 1 ↔ 3 | `PatientResponse` 필드 구성 |

---

## 12. 테스트 시나리오

| No | 요구사항 | 시나리오 | 기대 결과 | 담당 |
|---|---|---|---|---|
| T1 | REQ-PTNT-001 | 의료 부서 스태프가 환자 등록 | 201 | 팀원 1 |
| T2 | REQ-PTNT-001 | 개발 부서 스태프가 환자 등록 | 403 | 팀원 1 |
| T3 | REQ-PTNT-001 | 대기자가 환자 등록 | 403 | 팀원 1 |
| T4 | REQ-PTNT-001 | 나이 200, 연락처 `0101234` | 422 | 팀원 1 |
| T5 | REQ-PTNT-002 | 이름 + 성별 + 나이 범위 조합 검색 | 조건에 맞는 환자만 | 팀원 1 |
| T6 | REQ-PTNT-002 | `min_age=50&max_age=30` | 400 | 팀원 1 |
| T7 | REQ-PTNT-003 | 없는 환자 ID | 404 | 팀원 3 |
| T8 | REQ-PTNT-004 | 이름만 수정 | 이름만 바뀌고 `updated_at` 갱신 | 팀원 3 |
| T9 | REQ-PTNT-004 | `{"age": 50}` | 422 | 팀원 3 |
| T10 | REQ-PTNT-005 | 진료기록·이미지가 있는 환자 삭제 | 204, DB 행과 `storage/xray/{patient_id}/` 폴더 모두 삭제 | 팀원 3 |
| T11 | REQ-MDR-001 | PNG 업로드로 진료기록 등록 | 201, `xray_image_url`이 API 경로 | 팀원 2 |
| T12 | REQ-MDR-001 | 같은 차트 넘버로 재등록 | 409 | 팀원 2 |
| T13 | REQ-MDR-001 | PDF 업로드 / 11MB 이미지 | 415 / 413 | 팀원 2 |
| T14 | REQ-MDR-001 | 확장자만 `.png`로 바꾼 텍스트 파일 | 415 | 팀원 2 |
| T15 | REQ-MDR-002 | 증상 150자 기록 조회 | 100자 + `...` | 팀원 4 |
| T16 | REQ-MDR-003 | 상세 조회 | 증상 전체, `patient_id`, 이미지 API 경로 | 팀원 4 |
| T17 | REQ-MDR-003 | 토큰을 담아 이미지 조회 | 200, 이미지 표시 | 팀원 4 |
| T18 | 보안 | 토큰 **없이** 이미지 조회 | 401 | 팀원 4 |
| T19 | 보안 | 대기자 토큰으로 이미지 조회 | 403 | 팀원 4 |
| T20 | 보안 | `/media/xray/...` 등 직접 경로로 접근 | 404 (공개 경로에 파일 없음) | 팀원 4 |
| T21 | 공통 | 토큰 없이 API 요청 | 401 | 팀원 2 |
| T22 | REQ-PTNT-002 | 이름에 `%` 입력 | `%`가 들어간 이름만 검색 (전체 조회되지 않음) | 팀원 1 |
| T23 | REQ-MDR-001 | 같은 차트 넘버로 **동시에** 2건 등록 | 1건 201, 1건 409, 실패한 쪽의 이미지 파일이 남지 않음 | 팀원 2 |
| T24 | 수정 (추가) | AI 결과가 있는 진료기록의 이미지 교체 | 기존 이미지 행·파일과 AI 결과 삭제, 새 이미지로 조회됨 | 팀원 5 |
| T25 | REQ-PTNT-005 | SQLite 테스트 DB에서 환자 삭제 | `PRAGMA foreign_keys=ON` 상태에서 자식 행까지 삭제 | 팀원 3 |
| T26 | 수정 (추가) | 의료진이 증상만 수정 | 200, 증상만 바뀌고 `updated_at` 갱신 | 팀원 5 |
| T27 | 수정 (추가) | 다른 기록의 차트 넘버로 수정 | 409, 새로 저장한 파일이 남지 않음 | 팀원 5 |
| T28 | 삭제 (추가) | 진료기록 삭제 | 204, 이후 상세·이미지 조회 시 404, 이미지·히트맵 파일 삭제 | 팀원 5 |

---

## 13. 팀 결정이 필요한 사항

| No | 항목 | 이 문서의 제안 | 다른 선택지 | 고려할 점 |
|---|---|---|---|---|
| 1 | 진료기록 수정·삭제 (10~11번) | ✅ **결정 완료: 구현** (팀원 5) | 구현하지 않음 | 과제 안내문이 요구하고, 모든 팀원이 API를 1개 이상 맡아야 한다 |
| 2 | "의료인" 기준 | 어드민 또는 의료 부서 스태프 | 스태프 전체 | 요구사항이 등록만 "의료인"으로 구분 |
| 3 | **환자 삭제 권한** | 정의서대로 스태프 이상 | 의료진만 | 등록은 의료인만인데, 진료기록까지 영구 삭제하는 환자 삭제는 개발·연구진도 가능한 것이 의도인지 확인 필요 |
| 4 | **차트 넘버 중복 금지** | UNIQUE (현재 모델) | 환자 단위로만 중복 금지 | 정의서에 명시되지 않은 가정. 병원 규칙에 따라 다름 |
| 5 | X-Ray 이미지 보안 (D10) | 비공개 저장 + 인증 API | `media/` 공개 | 상세 화면 수정이 함께 필요 |
| 6 | `shooting_datetime` | 업로드 시각 | nullable로 변경 | 실제 촬영 일시와 다를 수 있음 |

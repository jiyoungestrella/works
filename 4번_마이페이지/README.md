# 4번 (김지영) 마이페이지 작업 백업

팀 레포 `thgPwls98/OZ_codingSchool`의 **main**(1번 #17, 2번 #18 머지 후) 기준으로 작업한 내용이다.
아직 팀 레포에는 올리지 않았다.

## API
| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/v1/users/me` | 내 정보 조회 |
| PATCH | `/api/v1/users/me` | 부서·휴대폰 번호 수정 |
| PATCH | `/api/v1/users/me/password` | 비밀번호 변경 (성공 시 리프레시 쿠키 삭제) |
| DELETE | `/api/v1/users/me` | 회원탈퇴 (X-ray는 보존, uploader_id SET NULL은 1번이 넣음) |

## 바뀐 파일 (모두 main 파일에 **추가만** 함)
- `app/apis/user_apis.py`: 라우터 4개 (2번의 `CurrentUser`, `_delete_refresh_cookie` 사용)
- `app/schemas/user.py`: `UpdateMeRequest`, `ChangePasswordRequest`
- `app/repositories/user_repository.py`: `save`, `delete`
- `app/services/user_service.py`: `update_me`, `change_password`, `delete_me`

## 팀 레포에 올리는 법 (내 PC)
```bash
git switch main && git pull
git switch -c feature/my-page
git am 경로/4번_마이페이지/patch/*.patch     # 안 되면 위 파일을 복사해 덮어쓴 뒤 커밋
git push -u origin feature/my-page
```
그 다음 Swagger(`/docs`)에서 Authorize로 로그인 후 4개 API 확인 → PR.

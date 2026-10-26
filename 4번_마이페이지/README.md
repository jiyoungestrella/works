# 4번 (김지영) 마이페이지 작업 백업

팀 레포 `thgPwls98/OZ_codingSchool`의 `feature/signup`(1번) 위에서 작업한 내용이다.
아직 팀 레포에는 올리지 않았다.

## 바뀐 파일
- `app/models/xray_image.py`: uploader_id NULL 허용 + ON DELETE SET NULL
- `alembic/versions/9f3b6d2a1c5e_xray_uploader_set_null.py`: 위 변경 마이그레이션 (1번 마이그레이션 7c1e2a9d4b10 다음)
- `app/schemas/user.py`: `UpdateMeRequest`, `ChangePasswordRequest` 추가
- `app/repositories/user_repository.py`: `save`, `delete` 추가
- `app/services/user_service.py`: `update_me`, `change_password`, `delete_me` 추가

`schemas/user.py`, `user_repository.py`, `user_service.py`는 1번 파일에 내 코드를 **아래에 추가**한 것이라
1번 코드가 바뀌면 통째로 덮어쓰지 말고 추가한 부분만 옮긴다.

## 팀 레포에 올리는 법 (내 PC)
```bash
git switch main && git pull
git switch -c feature/my-page origin/feature/signup   # 1번이 main에 머지됐으면 main에서
git am 경로/4번_마이페이지/patch/*.patch              # 또는 파일을 직접 복붙 후 커밋
git push -u origin feature/my-page
```

## 남은 일
- 2번(JWT) 머지 후: `get_current_user`로 라우터 4개 연결 (GET/PATCH/DELETE `/users/me`, PATCH `/users/me/password`), 비번 변경·탈퇴 시 refresh 쿠키 삭제
- Swagger 테스트 → PR

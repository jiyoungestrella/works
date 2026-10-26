# 4일차 TIL: FastAPI + SQLite 연결 (ORM, SQLAlchemy)

## 1. 오늘 배운 흐름 한눈에 보기

> **3일차의 `ITEMS` 리스트(메모리)를 DB(SQLite 파일)로 옮겼다. SQL을 직접 쓰지 않고, 파이썬 코드만 쓰면 ORM(SQLAlchemy)이 SQL로 바꿔서 DB에 반영해 준다.**

```text
클라이언트 ──요청──▶ FastAPI ──(ORM이 SQL로 통역)──▶ SQLite
           ◀─응답──          ◀────── 결과 ──────────
```

| 파일 | 역할 | 비유 |
|---|---|---|
| `connection.py` | **어떻게** 연결하나 (엔진, 세션) | 기록실로 가는 **통로** |
| `model.py` | **무엇을** 저장하나 (테이블 모양) | 기록실에 둘 **기록지 양식** |
| `main.py` | API에서 세션으로 DB를 조회·저장 | **접수 창구** |
| `fastapi.db` | 실제 데이터가 저장되는 파일 | **중앙 기록실** |

---

## 2. ORM (Object-Relational Mapping)

**SQL 직접 사용 ❌ → ORM으로 파이썬 코드만 쓴다**

DB는 SQL이라는 자기 언어만 알아듣는다. ORM은 파이썬과 DB 사이의 **통역사**다.

> 비유: 우리 병원(파이썬)은 한국어, 외부 검사실(DB)은 영어만 받는다. 매번 영어 의뢰서를 쓰는 대신 **전담 통역사(ORM)**를 둔다. 한국어로 말하면 영어 의뢰서로 바꿔 보내고, 결과도 한국어로 바꿔준다.

- **Object**: 파이썬의 객체 (클래스, 인스턴스)
- **Relational**: 관계형 DB의 표 (테이블)
- **Mapping**: 둘을 1:1로 짝지어 줌

### 짝짓는 규칙 3줄 ⭐

| DB | 파이썬 | 병원 비유 |
|---|---|---|
| 테이블 1개 | **클래스** 1개 | 환자기록지 **양식** |
| 행(row) 1개 | **인스턴스** 1개 | 양식으로 뽑은 **환자 한 명의 기록지** |
| 열(column) 1개 | **인스턴스 속성** 1개 | 기록지의 **칸** (이름 칸, 나이 칸) |

> 2일차 "클래스 = 기록지 양식, 인스턴스 = 환자 한 명의 기록지"가 DB 표와 그대로 맞아떨어진다.

### 파이썬만 쓰면 ORM이 알아서 SQL로

```text
우리가 쓰는 것 (파이썬)             ORM이 대신 만드는 것 (SQL)
Item(name="apple", price=100)  →  INSERT INTO item ...
select(Item)                   →  SELECT ... FROM item
item.price = 250               →  UPDATE item SET price=250 ...
session.delete(item)           →  DELETE FROM item WHERE ...
```

- SQL이 사라진 건 아니다. **뒤에서 만들어져 DB로 간다** (`echo=True`로 볼 수 있음).
- 바로 반영되는 건 아니다. **`commit()`(확정 도장)**을 해야 DB에 저장된다.

### 왜 쓰나?
1. SQL을 몰라도 파이썬 문법만으로 DB를 다룬다.
2. DB를 바꾸기 쉽다 (SQLite → PostgreSQL로 가도 코드는 거의 그대로).
3. 오타·타입 오류를 파이썬 단계에서 잡을 수 있다.
4. 거의 모든 언어에 ORM이 있다 (파이썬 SQLAlchemy, 자바 JPA, JS Prisma).

### SQLAlchemy
- **ORM** = 개념 (통역사라는 직업)
- **SQLAlchemy** = 파이썬에서 가장 많이 쓰는 ORM 라이브러리 (특정 통역 회사)
- 설치: `pip install sqlalchemy`
- 1.x와 2.0 문법이 다르다. 요즘은 2.0 문법(`select(...)`)을 쓴다. 옛날 예제의 `session.query(...)`와 헷갈리지 않기.

### 라이브러리는 자기만의 스타일이 있다 (opinionated)

| 역할 | 우리가 쓰는 것 | 다른 선택지 |
|---|---|---|
| 웹 프레임워크 | FastAPI | Django, Flask |
| ORM | SQLAlchemy | SQLModel, TortoiseORM |

> 비유: 같은 "환자 접수"라도 병원마다 전산 화면과 절차가 다르다. `sessionmaker`, `bind` 같은 이름은 "왜?"보다 **"SQLAlchemy식 표현"**으로 받아들이면 편하다. (It is what it is)

---

## 3. SQLite와 도구들

**SQLite = 설치 없이 쓸 수 있는 가벼운 DB**

1. 파이썬에 이미 들어 있다 (`sqlite3` 모듈).
2. 서버가 없다. **파일 하나(`xxx.db`)가 곧 DB**다.

> 비유:
> - **MySQL, PostgreSQL** = 담당 직원(서버)이 상주하는 **중앙 기록실**. 크고, 여러 부서가 동시에 쓰기 좋다.
> - **SQLite** = 진료실 책상 위 **기록 바인더 한 권**. 바로 펼쳐 쓰면 된다. 공부·테스트·작은 앱에 딱.

| 본체 | 도와주는 프로그램 | 역할 |
|---|---|---|
| python (언어) | VSCode | 코드를 편하게 **작성** |
| sqlite (DB) | DB Browser for SQLite | DB 파일 안을 표처럼 **눈으로 확인** |

> `.db` 파일은 **밀봉된 바인더**라 그냥 열면 글자가 깨진다. DB Browser는 표로 펼쳐 보여주는 **뷰어**다. (필수는 아니고 확인용)

### DB는 왜 "여러 곳에서" 쓰일까?
DB는 데이터의 **원천**이다. 서버 여러 대, 데이터 분석, 머신러닝이 **동시에** 같은 DB를 쓴다. 그래서 요청마다 따로 처리하는 **세션**이 필요하다.

> 비유: 중앙 의무기록실에 외래, 응급실, 연구팀, AI 판독팀이 동시에 찾아온다. 한 줄로 세우면 마비되니까 **요청마다 창구 번호표(세션)**를 준다.

---

## 4. connection.py: 연결 설정

```python
# ORM을 이용해서 데이터베이스에 연결할 때 사용하는 설정
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = "sqlite:///fastapi.db"

# 엔진
engine = create_engine(DATABASE_URL, echo=True)

# 세션
SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
```

### DATABASE_URL
- **DB 주소**: "어떤 DB(sqlite)의 어떤 파일(fastapi.db)인지"
- `sqlite:///` 뒤 = 현재 폴더 기준 파일 경로
- 파일이 없으면 **처음 연결할 때 자동 생성**

### 엔진 (engine)
- **DB와 실제로 연결되는 통로**. 모든 명령은 엔진을 거쳐 간다.
- `echo=True`: 엔진을 지나가는 **SQL을 터미널에 출력** → ORM이 만든 SQL을 눈으로 확인

> 비유: 엔진 = 병원과 기록실을 잇는 **기송관(서류 배달 통로)**, `echo=True` = 통로에 단 **CCTV**

### 세션 (session)
**세션 = 작업 한 건을 시작해서 끝낼 때까지의 기간.** 작업마다 세션이 하나씩 생겨서 동시다발 작업이 가능하다.

브라우저 Storage API로 "세션"이라는 단어 감 잡기:

| | 유지 기간 |
|---|---|
| Local Storage | 무기한 |
| Session Storage | **특정 탭이 활성화된 기간**만 |

> 비유: 환자 한 명의 **진료 한 회차**. 접수~수납이 세션 하나. 다른 환자와 섞이지 않는다.

### sessionmaker = 세션 공장 (팩토리)
- `sessionmaker(...)`는 **설정이 미리 박힌 세션 공장**을 만든다.
- 공장을 호출하면(`SessionFactory()`) **세션 인스턴스가 하나씩** 나온다.

```python
db1 = SessionFactory()   # 작업 1용 세션
db2 = SessionFactory()   # 작업 2용 세션 (별개)
```

> 비유: 진료 기록지 **인쇄기**를 한 번 세팅해 두고(용지, 서식), 환자 올 때마다 버튼만 누르면 같은 설정의 기록지가 한 장씩 나온다.

- `bind=engine`: 이 공장에서 나온 세션은 **이 엔진(통로)을 쓴다**고 연결 선언

### False 3개: 자동 동작은 끄고 타이밍은 내가 정한다

| 옵션 | 켜져 있으면 | 끄면 (`False`) |
|---|---|---|
| `autoflush` | 조회 전에 쌓인 변경을 DB에 자동으로 밀어넣음 | 내가 정할 때만 보냄 |
| `autocommit` | 명령마다 자동 저장 | **내가 `commit()` 해야 저장** |
| `expire_on_commit` | 저장 후 객체 값을 무효화 (다시 DB에서 읽음) | 저장 후에도 **값을 그대로 들고 있음** |

> 비유:
> - `autocommit=False`: 다 쓰고 **"확정" 도장(commit)**을 찍어야 제출된다. 도장 전이면 취소(rollback) 가능.
> - `autoflush=False`: 쓰다 만 메모를 멋대로 먼저 보내지 않는다.
> - `expire_on_commit=False`: 제출 후에도 **내 손에 사본이 남아** 응답으로 바로 돌려줄 수 있다.

> 결론: **팩토리에서 세션을 꺼내 명령을 넣으면, 세션이 엔진을 거쳐 DB에 전달해 준다.**

```text
SessionFactory ──찍어냄──▶ 세션 ──bind──▶ 엔진 ──▶ fastapi.db
(공장)                   (작업 1건)     (통로)     (DB 파일)
```

---

## 5. model.py: 클래스와 테이블 연결 정보

```python
# ORM의 클래스와 테이블 연결 정보
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


# 테이블 정의 부모 클래스
class Base(DeclarativeBase):
    pass

# item 테이블
class Item(Base):
    __tablename__ = "item"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(64))
    price: Mapped[int] = mapped_column(Integer)
```

### Base 클래스는 왜 만들까?
- **그냥 `class Item:`** → 순수 파이썬 클래스. DB는 모른다.
- **`class Item(Base):`** → Base의 SQLAlchemy 성질을 **상속**받아 **"너는 테이블"** 자격이 생긴다.

> 비유: 아무 종이에 적으면 메모, **병원 공식 서식 용지(Base)**에 적어야 의무기록으로 인정된다.

`DeclarativeBase`를 바로 안 쓰고 `Base`를 한 번 거치는 이유:
1. **명단 관리**: Base를 상속한 클래스는 하나의 명단(`Base.metadata`)에 등록 → 한 번에 테이블 생성 가능
2. **나중에 바꾸기 쉬움**: 지금은 `pass`(내용 없음)지만, 모든 테이블 공통 컬럼(예: 생성 시각)이 생기면 Base에만 추가

> 비유: 공식 서식의 **마스터 원본**. 로고를 바꾸고 싶으면 원본만 고친다.

### `__tablename__ = "item"`
DB 안에 만들어질 **테이블 이름**. 정의한 이름대로 만들어진다.

### 컬럼 정의 ⭐ 가장 중요

```python
price: Mapped[int] = mapped_column(Integer)
#      └ 파이썬 쪽 ┘   └──── DB 쪽 ────┘
```

| 부분 | 누구를 위한 것 | 의미 |
|---|---|---|
| `Mapped[int]` | 파이썬 / VS Code | "이 속성은 컬럼과 매핑되고, 꺼내면 int" (타입 힌트) |
| `mapped_column(Integer)` | DB | "DB에는 정수 칸으로 만들어" |

> 비유: 기록지 한 칸에 라벨 두 개. 직원용 한국어 라벨("나이: 숫자") + 기록실용 영어 라벨("AGE: INTEGER")

| 옵션 | 의미 |
|---|---|
| `primary_key=True` | **기본키**. 행 하나를 콕 집는 고유 번호 (= 환자 등록번호), 중복 불가 |
| `autoincrement=True` | 1, 2, 3…을 **DB가 알아서** 발급 |
| `String(64)` | 문자열, 최대 64글자 |

- "컬럼인 게 중요한 게 아니라 **어떤 타입인가**가 중요" → `Mapped[...]` 괄호 안의 타입이 핵심 정보
- **정적 분석**(코드를 실행하지 않고 미리 검사): `Mapped[int]`라고 적어두면 VS Code가 `item.price`를 int로 알아서 **자동완성**이 되고, 타입이 안 맞는 코드에 **미리 빨간 줄**을 그어준다.

> 비유: 처방전을 약국에 보내기 **전에** 전산이 "용량 단위가 이상해요" 하고 미리 경고해 준다.

### DB 컬럼에 타입을 고정하는 이유
1. **일관성**: price 칸엔 무조건 정수만. `100`, `"백원"`, `"100원"`이 섞이면 합계·정렬 불가
   > 체온 칸에 `36.5`와 `"미열"`이 섞이면 통계를 못 낸다.
2. **저장 효율성**: 칸마다 공간을 얼마나 잡을지 미리 알 수 있다 (메모리 사이즈 할당)
   > 서류함 칸 크기를 미리 정해두면 낭비 없이 꽂을 수 있다.

---

## 6. 테이블 생성: `create_all`

터미널에서 실행:

```bash
python -i model.py
```

- `python model.py`: 실행하고 **바로 종료**
- `python -i model.py`: 실행 후 **`>>>` 대화형 모드로 남음** (`-i` = interactive) → `Base`, `Item`이 메모리에 올라온 상태로 이어서 명령 가능
- `Base`를 치면 `<class '__main__.Base'>` (2일차에 본 "클래스 자체")

```python
>>> from connection import engine
>>> Base.metadata.create_all(bind=engine)
```

| 부분 | 의미 | 비유 |
|---|---|---|
| `Base` | 모든 테이블 클래스의 부모, 자식들을 한꺼번에 관리 | 서식 마스터 원본 |
| `.metadata` | Base를 상속한 테이블들의 **명단 + 설계 정보** | 서식 목록표 |
| `.create_all(...)` | 명단의 테이블을 **전부 생성** | "목록표의 서식 다 기록실에 등록!" |
| `bind=engine` | **어느 DB에** 만들지 | "이 통로로 연결된 기록실에" |

### 터미널 로그 읽기

```text
BEGIN (implicit)                  ← ① 작업 시작
PRAGMA main.table_info("item")    ← ② "item 테이블 이미 있어?" 확인
CREATE TABLE item (               ← ③ 없으니까 새로 만들기
    id INTEGER NOT NULL,
    name VARCHAR(64) NOT NULL,
    price INTEGER NOT NULL,
    PRIMARY KEY (id)
)
COMMIT                            ← ④ 확정 저장
```

| model.py | SQL | 뜻 |
|---|---|---|
| `__tablename__ = "item"` | `CREATE TABLE item` | 테이블 이름 |
| `Integer` | `INTEGER` | 정수 |
| `String(64)` | `VARCHAR(64)` | 최대 64글자 문자열 |
| `primary_key=True` | `PRIMARY KEY (id)` | 기본키 |
| `Mapped[int]` (`| None` 없음) | `NOT NULL` | **빈칸 금지** |

- `NOT NULL`은 안 적었는데 생겼다 → `Mapped[int]`에 `| None`이 없으면 "꼭 채워야 하는 칸"으로 해석. (`Mapped[int | None]`이면 빈칸 허용)
- `create_all`은 **없는 테이블만** 만든다 → 여러 번 실행해도 안전
- ⚠️ 반대로, model.py에 컬럼을 추가해도 **이미 있는 테이블은 안 바뀐다**

### 파일이 "뿅" 생긴 이유
connection.py에 주소만 적어뒀다가, `create_all`이 **처음 실제로 연결하는 순간** SQLite가 파일을 새로 만들었다. 빈 테이블 구조만 있어서 8KB.

> 비유: 바인더 이름표만 정해뒀다가, **첫 기록을 꽂으려는 순간** 빈 바인더가 생긴 것

### DB Browser로 확인
`Open Database` → `fastapi.db` → **Database Structure** 탭에 `item` 테이블과 `id INTEGER`, `name VARCHAR(64)`, `price INTEGER`가 정의한 그대로 보인다. 데이터는 **Browse Data** 탭에서 확인.

> DB Browser가 파일을 열고 있으면 **잠금**이 걸릴 수 있다. FastAPI에서 저장 에러가 나면 닫았다가 다시 열어볼 것.

---

## 7. 데이터 추가 (INSERT)

```python
>>> from connection import SessionFactory
>>> session = SessionFactory()               # ① 공장에서 세션 하나 꺼내기
>>> item = Item(name="apple", price=100)     # ② 넣을 데이터를 객체로 (= 행 1개)
>>> session.add(item)                        # ③ 세션 장바구니에 담기 (아직 DB X)
>>> session.commit()                         # ④ 확정! → 이때 실제로 DB에 저장
```

> 비유: ① 진료 번호표 뽑기 → ② 기록지 한 장 작성 → ③ 결재함에 넣기 → ④ **확정 도장** 찍는 순간 기록실로

| | 하는 일 | DB에 반영? |
|---|---|---|
| `session.add(item)` | "이거 저장할 거야" 하고 담아만 둠 | ❌ 아직 (로그 안 찍힘) |
| `session.commit()` | 담아둔 걸 한꺼번에 확정 | ✅ 이때 |

→ `add`와 `commit`이 나뉜 건 connection.py에서 `autocommit=False`로 꺼둔 효과

### 로그 읽기

```text
BEGIN (implicit)
INSERT INTO item (name, price) VALUES (?, ?) RETURNING id
[generated in 0.00047s] ('apple', 100)
COMMIT
```

- `INSERT INTO` = 데이터를 테이블에 추가하는 쿼리
- **`?` (빈칸 방식)**: 값을 SQL 문장에 직접 박지 않고 따로 전달 → **SQL 인젝션 방지** (보안)
  > 처방전 빈칸에 "그리고 마약장 열어"라고 써도 약 이름으로만 읽히지, 명령으로 실행되지 않는다.

### id는 DB가 자동 발급 + `RETURNING id`
- `name`, `price`는 우리가 줬지만 **`id`는 안 줬다** → `autoincrement`라서 DB가 저장 순간 발급
- 파이썬 쪽 `item` 객체는 번호를 모르니까, ORM이 **"매긴 id 알려줘"(`RETURNING id`)**라고 요청해서 `item.id`에 채워 넣는다.

```text
DB가 id 발급 → RETURNING id로 돌려줌 → item.id에 저장
```

> 비유: 기록지를 제출하면 원무과가 **등록번호를 발급**한다. 내 사본엔 번호가 비어 있으니 "발급한 번호 불러주세요" 하고 받아 적는 것

| | 3일차 (리스트) | 지금 (DB) |
|---|---|---|
| id 만드는 법 | 직접 계산 `len(ITEMS) + 1` | **DB가 자동 발급** |
| 문제점 | 중간 삭제 후 추가하면 **번호가 겹칠 수 있음** | 겹치지 않게 DB가 관리 |

→ 등록 API 응답에 새 id까지 돌려줘야 하니까 `RETURNING id`가 필요하다.

### 여러 개 한 번에 추가 (트랜잭션)

```python
>>> item2 = Item(name="banana", price=200)
>>> item3 = Item(name="cherry", price=300)
>>> session.add(item2)
>>> session.add(item3)
>>> session.commit()     # 결제는 한 번
```

- 묶은 작업 단위 = **트랜잭션**. **전부 성공하거나, 전부 실패**한다.
  > 입원 수속(병실, 처방, 식단)을 한 묶음으로. 병실 배정이 실패했는데 식단만 등록되면 곤란하다.
- 로그의 `insertmanyvalues 1/2, 2/2 (batch not supported)`: id를 순서대로 돌려받아야 해서 INSERT는 **하나씩** 보냈지만, commit은 한 번이라 "전부 성공 또는 전부 실패"는 그대로
- `session.add_all([item2, item3])`로 리스트째 담을 수도 있다.

### 다 끝나면 `session.close()`

```python
session.close()   # 세션 반납
```

- 세션은 열려 있는 동안 DB 연결을 붙잡고 있다. 안 닫으면 자원 낭비 + SQLite 파일 잠금 가능

> 비유: 진료가 끝나면 **번호표를 반납하고 창구를 비워야** 다음 환자가 쓸 수 있다.

| | 의미 | 비유 |
|---|---|---|
| `commit()` | 작업 내용 **확정 저장** | 확정 도장 찍기 |
| `close()` | 세션 **반납** | 번호표 반납, 창구 비우기 |

→ 순서는 항상 **commit → close**. commit 없이 close하면 담아둔 내용은 사라진다.

---

## 8. 데이터 조회 (SELECT)

```python
>>> from sqlalchemy import select
>>> stmt = select(Item)
>>> # SELECT * FROM item;
>>> stmt = select(Item.id, Item.name, Item.price)
>>> # SELECT id, name, price FROM item;
>>> print(stmt)                      # ORM이 만든 SQL 미리 보기
>>> result = session.execute(stmt)   # 실제로 DB에 제출
```

| 단계 | 의미 | 비유 |
|---|---|---|
| `stmt = select(...)` | **조회 요청서 작성** (아직 DB 안 감, 로그 X) | 조회 의뢰서 작성 |
| `print(stmt)` | 어떤 SQL로 바뀌는지 확인 | 의뢰서 미리 보기 |
| `session.execute(stmt)` | DB에 제출 → `SELECT` 실행 | 의뢰서 제출 |

- `stmt` = **statement(문장)**
- `select(Item)`: 테이블 **통째로** / `select(Item.id, Item.name)`: **원하는 칸만**
  > "기록지 전체 복사해 주세요" vs "이름이랑 나이 칸만 알려주세요"
- **조회는 commit 필요 없음**: 읽기만 하니까 확정할 게 없다 (열람엔 도장 불필요)

| 작업 | 쓰는 것 | commit 필요? |
|---|---|---|
| 추가 | `session.add()` | ✅ |
| 조회 | `select()` + `session.execute()` | ❌ |

### 결과 상자에서 꺼내기

`print(result)` → `<sqlalchemy.engine.result.ChunkedIteratorResult object at 0x...>`
결과는 **밀봉된 봉투(결과 상자)**라서 꺼내는 메서드가 필요하다.

| 조회 | 꺼내기 | 결과 모양 | 비유 |
|---|---|---|---|
| `select(Item.id, Item.name, Item.price)` | `.all()` | 튜플 리스트 `[(1, 'apple', 100), ...]` | 숫자만 나열된 결과 |
| 〃 | `.mappings().all()` | 딕셔너리 리스트 `[{'id': 1, 'name': 'apple', 'price': 100}, ...]` | 항목명 붙은 결과지 |
| `select(Item)` | `.scalars().all()` | **Item 객체 리스트** | 기록지 원본 묶음 |
| `select(Item).where(...)` | `.scalar()` | **Item 객체 하나** (없으면 `None`) | 기록지 한 장 |

- `.all()` = 상자 안의 **전부** 꺼내 리스트로
- `.mappings()` = 꺼내기 전에 **칸 이름표를 붙여서** → 딕셔너리 (3일차 `ITEMS`와 같은 모양)
- ⚠️ 결과 상자는 **한 번 꺼내면 빈다**. 다시 보려면 다시 `execute`
- 같은 `stmt`를 다시 실행하면 로그가 `[generated in ...]` → `[cached since 237.2s ago]`: 번역해 둔 SQL을 **재사용** (자주 쓰는 의뢰서 서식 저장)

### `scalars()`는 변환이 아니라 "꺼내기"

```text
.all()            → [(Item1,), (Item2,), ...]   ← 객체가 투명 파일 안에
.scalars().all()  → [Item1, Item2, ...]         ← 파일만 벗김
```

- **무엇을 받을지**(객체 / 값)는 `select(...)` 안에 뭘 넣느냐가 정한다.
- `scalars()`는 각 행의 **첫 번째 칸 알맹이만** 꺼낼 뿐
- 증거: `select(Item.name)` + `.scalars().all()` → `['apple', 'banana', 'cherry']` (객체가 아니라 문자열)

> 비유: 택배 상자를 뜯는 사람(`scalars`)은 안에 든 걸 꺼내기만 한다. 뭘 넣을지는 **주문서(`select`)를 쓸 때** 정해진다.

### 객체로 받으면 좋은 점
객체는 주소만 보이지만(`<__main__.Item object at 0x...>`), **속성(점)**으로 내용을 꺼낸다.

```python
>>> items = result.scalars().all()
>>> items[0].name
'apple'
```

1. 점(.)으로 편하게 읽는다 → "1개 열 = 1개 인스턴스 속성"
2. **고쳐서 그대로 저장**할 수 있다 (`item.price = 150` → `commit()` → UPDATE)
3. FastAPI `response_model`로 바로 응답할 수 있다

> 튜플·딕셔너리는 **복사본**, 객체는 **원본 기록지**. 원본을 고치고 도장을 찍으면 기록실에 반영된다.

→ 실무에서는 **`select(Item)` + `.scalars().all()` / `.scalar()`** 조합을 가장 많이 쓴다.

### 조건 조회: `.where()` + `scalar()`

```python
>>> stmt = select(Item).where(Item.name == "apple")
>>> print(stmt)
SELECT item.id, item.name, item.price
FROM item
WHERE item.name = :name_1
>>> result = session.execute(stmt)
>>> result.scalar()
```

- `.where(...)` = **"그중에 이 조건에 맞는 것만"** (3일차의 `for` + `if`를 DB가 대신)
- 파이썬 비교 `==` → SQL 비교 `=` 로 ORM이 바꿔준다
- `:name_1`(print 때) / `?`(실행 때) = INSERT 때와 같은 **빈칸 방식**
- **`scalar()` = 하나, `scalars()` = 여러 개**

| 메서드 | 0개 | 1개 | 여러 개 |
|---|---|---|---|
| `scalar()` | `None` | 그거 | **첫 번째만 (조용히)** |
| `scalar_one()` | 에러 | 그거 | 에러 |
| `scalar_one_or_none()` | `None` | 그거 | 에러 |

---

## 9. main.py를 DB 버전으로 바꾸기

### import 추가

```python
from fastapi import FastAPI, Path, Query, Body, HTTPException
from pydantic import BaseModel, Field

#db====================
from connection import SessionFactory
from sqlalchemy import select
from model import Item
#=====================
```

### 각 API (오타 수정 반영)

```python
# 전체 상품 조회
def get_items_handler():
    session = SessionFactory()

    stmt = select(Item)
    result = session.execute(stmt)
    items: list[Item] = result.scalars().all()
    return items


# 상품 검색
def search_items_handler(
    q: str = Query(..., min_length=2),
    sort: str = Query(...),
):
    session = SessionFactory()

    stmt = select(Item).where(Item.name.contains(q))   # contains (s 주의)
    result = session.execute(stmt)
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=404, detail="검색 결과가 없음")
    return items


# 단일 상품 조회
def get_item_detail_handler(
    item_id: int = Path(..., ge=1)
):
    session = SessionFactory()

    stmt = select(Item).where(Item.id == item_id)
    result = session.execute(stmt)
    # id라 0 or 1 → 단수 → 행 하나만 꺼내는 함수
    item = result.scalar()

    if not item:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없음")
    return item


# 새로운 상품 등록
def create_new_item_handler(body: CreateItemRequest):
    session = SessionFactory()

    new_item = Item(name=body.name, price=body.price)
    session.add(new_item)
    session.commit()   # DB 저장하면서 id 자동으로 넣어줌: RETURNING id
    return new_item


# 상품 수정
def update_item_handler(
    item_id: int = Path(..., ge=1),
    body: UpdateItemRequest = Body(...),
):
    session = SessionFactory()
    # 조회
    stmt = select(Item).where(Item.id == item_id)
    result = session.execute(stmt)
    item = result.scalar()
    if not item:
        raise HTTPException(status_code=404, detail="상품 not found.")
    # 수정
    if body.name:
        item.name = body.name
    if body.price:
        item.price = body.price

    session.commit()
    return item


# 상품 삭제
def delete_item_handler(
    item_id: int = Path(..., ge=1),
):
    session = SessionFactory()

    stmt = select(Item).where(Item.id == item_id)
    result = session.execute(stmt)
    item = result.scalar()
    if not item:
        raise HTTPException(status_code=404, detail="상품을 찾을 수 없습니다.")

    session.delete(item)
    session.commit()
    # return은 빈 리턴으로 자동처리됨
```

- 수정은 **객체 속성만 바꾸고 commit** → ORM이 UPDATE로 바꿔준다 (`item["price"]` → `item.price`)
- 데코레이터(`@app.get(...)` 등)는 3일차 그대로
- 남은 숙제: 세션을 열기만 하고 `close()`를 안 함 → 요청마다 자동으로 열고 닫는 방법은 다음에
- 3일차 주의 그대로: `if body.price:`는 0이면 수정 안 됨 → 0도 허용하려면 `is not None`

### 리스트 → DB 바뀐 점

| 작업 | 3일차 (리스트) | 4일차 (DB) |
|---|---|---|
| 전체 조회 | `return ITEMS` | `select(Item)` → `scalars().all()` |
| 검색 | `for` + `if q in item["name"]` | `.where(Item.name.contains(q))` |
| 하나 찾기 | `for` + `if item["id"] == item_id` | `.where(Item.id == item_id)` → `scalar()` |
| 추가 | `ITEMS.append(...)` + id 직접 계산 | `session.add()` + `commit()` (id 자동) |
| 수정 | `item["price"] = ...` | `item.price = ...` + `commit()` |
| 삭제 | `ITEMS.remove(item)` | `session.delete(item)` + `commit()` |

### `ITEMS` 리스트는 이제 안 쓴다
- `Item` 클래스는 **양식**(모양만 정의)이지 데이터가 아니다.
- 실제 데이터는 **`fastapi.db` 파일 안**에 있다 (터미널에서 add + commit으로 넣은 것).
- 모든 함수가 **세션을 통해 DB에서** 꺼내니까 `ITEMS`는 아무도 안 보는 변수 → 지워도 된다.

> 비유: 예전엔 **책상 위 메모지**(ITEMS)를 봤고, 이제는 **중앙 기록실**(DB)에 조회한다. 메모지는 버려도 된다.

### 3일차와 가장 큰 차이
서버를 껐다 켜도 **데이터가 남아 있다.** 데이터가 메모리가 아니라 파일(DB)에 저장되기 때문이다.

---

## 10. 오늘 만난 오류와 해결

| 위치 | 잘못 쓴 것 | 고친 것 | 증상 |
|---|---|---|---|
| 수정 API | `body: Updat eItemRequest` | `UpdateItemRequest` | 클래스 이름 띄어쓰기 → SyntaxError (서버 안 켜짐) |
| 수정 API | `status_code=404.` | `status_code=404,` | 쉼표 대신 마침표 → SyntaxError |
| 등록 API | `Item(name-body.name, ...)` | `Item(name=body.name, ...)` | `=` 대신 `-` → NameError |
| 검색 API | `Item.name.contain(q)` | `Item.name.contains(q)` | s 누락 → AttributeError |
| 단일 조회 API | `item = ...scalar()` 후 `if not items` | `if not item` / `return item` | 단수·복수 이름 불일치 → NameError |
| 수정 API | `itme.price` | `item.price` | 철자 순서 → NameError |
| 삭제 API | `session.excute(stmt)` | `session.execute(stmt)` | e 누락 → AttributeError |
| 수정 API | `return item` 아래 남은 `raise HTTPException` | 삭제 | 절대 실행 안 되는 코드 |

### 팁
- **`scalars().all()` → 여러 개라 `items`**, **`scalar()` → 하나라 `item`**. 이름만 봐도 개수를 알 수 있게 맞추기
- VS Code 왼쪽 아래 ⓧ(에러) ⚠(경고) 숫자와 **빨간·노란 물결 밑줄**부터 확인
- SyntaxError는 서버가 아예 안 켜지고, NameError·AttributeError는 **그 API를 호출할 때** 500 에러로 터진다.

### 확인 순서
1. `fastapi dev`로 서버 켜기
2. `/docs`에서 **등록 → 전체 조회 → 검색 → 단일 조회 → 수정 → 삭제**
3. DB Browser **Browse Data** 새로고침으로 실제 반영 확인
4. 서버를 껐다 켜도 데이터가 남아 있으면 성공

---

## 11. 랩업

### 오늘 한 줄 요약
> **ORM(SQLAlchemy)으로 SQL 없이 파이썬만으로 SQLite를 다뤘다. connection.py에 엔진(통로)과 세션 공장을, model.py에 Base를 상속한 테이블 클래스(양식)를 만들고, `create_all`로 테이블을 생성했다. 세션으로 `add` + `commit`해서 저장하고, `select` + `execute` + `scalars`/`scalar`로 조회했다. main.py의 `ITEMS` 리스트를 DB로 바꿔서, 이제 서버를 껐다 켜도 데이터가 남는다.**

### 오늘 기억할 핵심 5가지
1. **테이블 = 클래스, 행 = 인스턴스, 열 = 인스턴스 속성** (ORM의 짝짓기)
2. **엔진** = DB로 가는 통로, **세션** = 작업 한 건, **SessionFactory** = 세션 공장
3. 컬럼은 `Mapped[파이썬 타입] = mapped_column(DB 타입)`. 타입 고정 = 일관성 + 저장 효율성
4. **저장**: `add` → `commit` (→ `close`) / **조회**: `select` → `execute` → 꺼내기 (commit 불필요)
5. **`scalars().all()` = 여러 개 리스트, `scalar()` = 하나** (없으면 `None` → 404)

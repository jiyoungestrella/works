"""xray_images.uploader_id nullable + ON DELETE SET NULL

회원탈퇴(REQ-USER-009) 시 사용자 행만 삭제하고 X-ray는 보존하기 위해
uploader_id를 NULL 허용으로 바꾸고 외래키에 ON DELETE SET NULL을 적용한다.

Revision ID: 9f3b6d2a1c5e
Revises: 7c1e2a9d4b10
Create Date: 2026-10-26 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f3b6d2a1c5e"
down_revision: Union[str, Sequence[str], None] = "7c1e2a9d4b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_NAME = "fk_xray_images_uploader_id_users"


def _drop_uploader_fk() -> None:
    # 초기 마이그레이션에서 이름 없이 만든 외래키(MySQL 자동 이름)를 찾아 삭제한다.
    inspector = sa.inspect(op.get_bind())
    for fk in inspector.get_foreign_keys("xray_images"):
        if fk["constrained_columns"] == ["uploader_id"]:
            op.drop_constraint(fk["name"], "xray_images", type_="foreignkey")


def upgrade() -> None:
    """Upgrade schema."""
    _drop_uploader_fk()
    op.alter_column(
        "xray_images",
        "uploader_id",
        existing_type=sa.Integer(),
        nullable=True,
        existing_comment="업로드한 의료진 ID",
        comment="업로드한 의료진 ID (탈퇴 시 NULL)",
    )
    op.create_foreign_key(FK_NAME, "xray_images", "users", ["uploader_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    """Downgrade schema.

    uploader_id가 NULL인 행(탈퇴한 사용자의 X-ray)이 있으면 실패한다.
    """
    _drop_uploader_fk()
    op.alter_column(
        "xray_images",
        "uploader_id",
        existing_type=sa.Integer(),
        nullable=False,
        existing_comment="업로드한 의료진 ID (탈퇴 시 NULL)",
        comment="업로드한 의료진 ID",
    )
    op.create_foreign_key(FK_NAME, "xray_images", "users", ["uploader_id"], ["id"])

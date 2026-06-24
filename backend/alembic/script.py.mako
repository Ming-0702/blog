"""Alembic 迁移脚本模板"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "{{ revision }}"
down_revision: Union[str, None] = "{{ down_revision }}"
branch_labels: Union[str, Sequence[str], None] = "{{ branch_labels }}"
depends_on: Union[str, Sequence[str], None] = "{{ depends_on }}"


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

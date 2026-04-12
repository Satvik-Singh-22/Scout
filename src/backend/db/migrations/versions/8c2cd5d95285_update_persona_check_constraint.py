# Copyright 2026 The SCOUT Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""update_persona_check_constraint

Revision ID: 8c2cd5d95285
Revises: a1b2c3d4e5f6
Create Date: 2026-04-12 12:58:01.610538

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c2cd5d95285'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop old constraint first so we can update the data
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_persona")
    
    # 2. Update existing data if any
    op.execute("UPDATE users SET persona = 'EXECUTIVE' WHERE persona = 'MANAGER'")
    op.execute("UPDATE users SET persona = 'TECHNICAL' WHERE persona = 'DEVELOPER'")
    
    # 3. Add new constraint
    op.create_check_constraint(
        'ck_users_persona',
        'users',
        "persona IN ('EXECUTIVE', 'TECHNICAL')"
    )


def downgrade() -> None:
    # 1. Drop new constraint
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_persona")
    
    # 2. Revert data
    op.execute("UPDATE users SET persona = 'MANAGER' WHERE persona = 'EXECUTIVE'")
    op.execute("UPDATE users SET persona = 'DEVELOPER' WHERE persona = 'TECHNICAL'")
    
    # 3. Add old constraint
    op.create_check_constraint(
        'ck_users_persona',
        'users',
        "persona IN ('MANAGER', 'DEVELOPER')"
    )

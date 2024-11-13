"""Add frequency to transaction

Revision ID: 2dea4f47dc33
Revises: 
Create Date: 2024-11-13 14:35:22.279260

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2dea4f47dc33"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("transaction", schema=None) as batch_op:
        batch_op.add_column(sa.Column("frequency", sa.String(length=20), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("transaction", schema=None) as batch_op:
        batch_op.drop_column("frequency")

    # ### end Alembic commands ###

"""trace_logs

Revision ID: a1c123cf4fe2
Revises: 12aff95665e0
Create Date: 2024-11-20 13:36:41.998354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision: str = 'a1c123cf4fe2'
down_revision: Union[str, None] = '12aff95665e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('trace_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ts', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('env', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('server_ip', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('client_addr', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('method', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('conversation_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('message_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('req_timestamp', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('trace_tree', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trace_conv_msg', 'trace_logs', ['conversation_id', 'message_id'], unique=False)
    op.create_index('idx_trace_env_ts', 'trace_logs', ['env', 'ts'], unique=False)
    op.create_index('idx_trace_method_ts', 'trace_logs', ['method', 'ts'], unique=False)
    op.create_index(op.f('ix_trace_logs_client_addr'), 'trace_logs', ['client_addr'], unique=False)
    op.create_index(op.f('ix_trace_logs_conversation_id'), 'trace_logs', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_trace_logs_env'), 'trace_logs', ['env'], unique=False)
    op.create_index(op.f('ix_trace_logs_message_id'), 'trace_logs', ['message_id'], unique=False)
    op.create_index(op.f('ix_trace_logs_method'), 'trace_logs', ['method'], unique=False)
    op.create_index(op.f('ix_trace_logs_req_timestamp'), 'trace_logs', ['req_timestamp'], unique=False)
    op.create_index(op.f('ix_trace_logs_server_ip'), 'trace_logs', ['server_ip'], unique=False)
    op.create_index(op.f('ix_trace_logs_ts'), 'trace_logs', ['ts'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_trace_logs_ts'), table_name='trace_logs')
    op.drop_index(op.f('ix_trace_logs_server_ip'), table_name='trace_logs')
    op.drop_index(op.f('ix_trace_logs_req_timestamp'), table_name='trace_logs')
    op.drop_index(op.f('ix_trace_logs_method'), table_name='trace_logs')
    op.drop_index(op.f('ix_trace_logs_message_id'), table_name='trace_logs')
    op.drop_index(op.f('ix_trace_logs_env'), table_name='trace_logs')
    op.drop_index(op.f('ix_trace_logs_conversation_id'), table_name='trace_logs')
    op.drop_index(op.f('ix_trace_logs_client_addr'), table_name='trace_logs')
    op.drop_index('idx_trace_method_ts', table_name='trace_logs')
    op.drop_index('idx_trace_env_ts', table_name='trace_logs')
    op.drop_index('idx_trace_conv_msg', table_name='trace_logs')
    op.drop_table('trace_logs')
    # ### end Alembic commands ###
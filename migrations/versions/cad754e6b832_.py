"""empty message

Revision ID: cad754e6b832
Revises: ce7bfcdd21fc
Create Date: 2020-04-17 21:46:45.962122

"""

# revision identifiers, used by Alembic.
revision = 'cad754e6b832'
down_revision = 'ce7bfcdd21fc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    article_type = postgresql.ENUM('text', 'image', 'video', name='articletype')
    article_type.create(op.get_bind())
    op.add_column('article', sa.Column('article_type', sa.Enum('text', 'image', 'video', name='articletype'), nullable=True, default='text'))
    op.create_index('ix_cluster_uid_martid', 'cluster', ['user_id', sa.text('main_article_id NULLS FIRST')], unique=False)
    op.drop_index('ix_cluster_martid', table_name='cluster')
    op.create_index('ix_cluster_martid', 'cluster', [sa.text('main_article_id NULLS LAST')], unique=False)
    op.drop_index('cluster_main_aid', table_name='cluster')
    op.drop_index('cluster_uid_maid', table_name='cluster')
    article_type = postgresql.ENUM('active', 'inactive', 'archive', name='articletype')

    feedtype = postgresql.ENUM('classic', 'json', 'tumblr', 'instagram', 'soundcloud', 'reddit', 'fetch', 'koreus', 'twitter', name='feedtype')
    feedstatus = postgresql.ENUM('active', 'paused', 'to_delete', 'deleting', name='feedstatus')
    feedtype.create(op.get_bind())
    feedstatus.create(op.get_bind())
    op.add_column('feed', sa.Column('feed_type', sa.Enum('classic', 'json', 'tumblr', 'instagram', 'soundcloud', 'reddit', 'fetch', 'koreus', 'twitter', name='feedtype'), nullable=False, default='classic'))
    op.add_column('feed', sa.Column('status', sa.Enum('active', 'paused', 'to_delete', 'deleting', name='feedstatus'), default='active', nullable=True))
    op.drop_column('feed', 'integration_reddit')
    op.drop_column('feed', 'readability_auto_parse')
    op.drop_column('feed', 'enabled')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('feed', sa.Column('enabled', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=True))
    op.add_column('feed', sa.Column('readability_auto_parse', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('feed', sa.Column('integration_reddit', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('feed', 'status')
    op.drop_column('feed', 'feed_type')
    op.create_index('cluster_uid_maid', 'cluster', ['user_id', 'main_article_id'], unique=False)
    op.create_index('cluster_main_aid', 'cluster', ['main_article_id'], unique=False)
    op.drop_index('ix_cluster_martid', table_name='cluster')
    op.create_index('ix_cluster_martid', 'cluster', ['user_id', 'main_article_id'], unique=False)
    op.drop_index('ix_cluster_uid_martid', table_name='cluster')
    op.drop_column('article', 'article_type')
    # ### end Alembic commands ###

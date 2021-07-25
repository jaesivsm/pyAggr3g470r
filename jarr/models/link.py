from enum import Enum as PythonEnum

from jarr.bootstrap import Base
from sqlalchemy import (Binary, Column, Enum, ForeignKeyConstraint, Index,
                        Integer, PickleType, String)
from sqlalchemy.orm import relationship


class LinkType(PythonEnum):
    main = 'main'
    attachment = 'attachment'


class LinkByArticleId(Base):
    __tablename__ = 'link_by_article_id'
    user_id = Column(Integer, primary_key=True, nullable=False)
    article_id = Column(Integer, primary_key=True, nullable=False)
    link_hash = Column(Binary, primary_key=True, nullable=False)

    user = relationship('User', back_populates='link_by_article_ids',
                        foreign_keys=[user_id])
    article = relationship('Article',
                           foreign_keys=[user_id, article_id])
    link = relationship('Link',
                        foreign_keys=[user_id, link_hash])

    __table_args__ = (
        ForeignKeyConstraint([link_hash], ['link.link_hash'],
                             ondelete='CASCADE'),
        ForeignKeyConstraint([article_id], ['article.id'], ondelete='CASCADE'),
        ForeignKeyConstraint([user_id], ['user.id'], ondelete='CASCADE'),
    )


class Link(Base):
    __tablename__ = 'link'

    user_id = Column(Integer, primary_key=True, nullable=False)
    link_hash = Column(Binary, primary_key=True, nullable=False)
    link = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    link_type = Column(Enum(LinkType), nullable=False)

    # relationships
    user = relationship(
        'User', back_populates='links', foreign_keys=[user_id])
    articles = relationship(
        'Article', back_populates='links', secondary='link_by_article_id',
        foreign_keys=[LinkByArticleId.article_id, LinkByArticleId.user_id,
                      LinkByArticleId.link_hash])

    __table_args__ = (
        ForeignKeyConstraint([user_id], ['user.id'], ondelete='CASCADE'),
        ForeignKeyConstraint([link_hash], [LinkByArticleId.link_hash],
                             ondelete='CASCADE'),
        Index('ix_link_uid_lhash', user_id, link_hash),
    )



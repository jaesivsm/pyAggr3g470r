import logging
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta, timezone

import dateutil.parser
from sqlalchemy import and_, func
from sqlalchemy.sql import delete, select
from werkzeug.exceptions import Forbidden

from jarr.bootstrap import conf, session
from jarr.controllers.abstract import AbstractController
from jarr.controllers.icon import IconController
from jarr.lib.const import UNIX_START
from jarr.lib.enums import FeedStatus
from jarr.lib.utils import utc_now
from jarr.metrics import FEED_EXPIRES, FEED_LATENESS
from jarr.models import Article, Category, Cluster, Feed, User

logger = logging.getLogger(__name__)
SPAN_FACTOR = 2
LIST_W_CATEG_MAPPING = OrderedDict((('id', Feed.id),
                                    ('str', Feed.title),
                                    ('icon_url', Feed.icon_url),
                                    ('category_id', Feed.category_id),
                                    ('last_retrieved', Feed.last_retrieved),
                                    ('error_count', Feed.error_count),
                                    ('last_error', Feed.last_error),
                                    ))


class FeedController(AbstractController):
    _db_cls = Feed

    @property
    def __actrl(self):
        from .article import ArticleController
        return ArticleController(self.user_id)

    def _set_unread_count(self, filters: set, fctr: int):
        filters.add(Cluster.user_id == Article.user_id)
        if self.user_id:
            filters.add(Cluster.user_id == self.user_id)
            filters.add(Article.user_id == self.user_id)
        q = session.query(Article.feed_id, func.count(Article.id))\
            .join(Cluster, and_(Cluster.id == Article.cluster_id, *filters))\
            .group_by(Article.feed_id)
        counts = defaultdict(list)
        for fid, cnt in q:
            counts[cnt].append(fid)
        for cnt, fids in counts.items():
            self.update({'id__in': fids},
                        {Feed.unread_count: Feed.unread_count + (cnt * fctr)})

    def decrease_unread_count(self, filters: set):
        filters.add(Cluster.read.__eq__(False))
        self._set_unread_count(filters, -1)

    def increase_unread_count(self, filters: set):
        filters.add(Cluster.read.__eq__(True))
        self._set_unread_count(filters, 1)

    def list_w_categ(self):
        feeds = defaultdict(list)
        for row in session.query(*LIST_W_CATEG_MAPPING.values())\
                .filter(Feed.user_id == self.user_id,
                        Feed.status != FeedStatus.to_delete,
                        Feed.status != FeedStatus.deleting)\
                .order_by(Feed.title):
            row = dict(zip(LIST_W_CATEG_MAPPING, row))
            row['type'] = 'feed'
            feeds[row['category_id']].append(row)
        yield {'id': None, 'str': None, 'type': 'all-categ'}
        yield from feeds.get(None, [])
        for cid, cname in session.query(Category.id, Category.name)\
                .filter(Category.user_id == self.user_id)\
                .order_by(Category.name.nullsfirst()):
            yield {'id': cid, 'str': cname, 'type': 'categ'}
            yield from feeds.get(cid, [])

    def get_active_feed(self, **filters):
        filters['error_count__lt'] = conf.feed.error_max
        query = self.read(status=FeedStatus.active, **filters)
        if conf.feed.stop_fetch:
            last_conn = utc_now() - timedelta(days=conf.feed.stop_fetch)
            return query.join(User).filter(User.is_active.__eq__(True),
                                           User.last_connection >= last_conn)
        return query

    def list_late(self, limit=0):
        """Will list either late feeds or feeds with articles recently created.

        Late feeds are feeds which have been retrieved for the last time sooner
        than now minus the delta (default to 1h). The others are feeds with
        article created later than now minus a quarter the delta (default to
        15 logically).

        The idea is to keep very active feed up to date and to avoid missing
        articles du to high activity (when, for example, the feed only displays
        its 30 last entries and produces more than one per minutes).

        Feeds of inactive (not connected for more than a month) or manually
        desactivated users are ignored.
        """
        now = utc_now()
        min_expiring = now - timedelta(seconds=conf.feed.min_expires)
        max_expiring = now - timedelta(seconds=conf.feed.max_expires)
        filters = self._to_filters(
            last_retrieved__lt=min_expiring,
            __or__=[{'expires__lt': now, 'expires__ne': None},
                    {'last_retrieved__lt': max_expiring,
                     'last_retrieved__ne': None}])
        query = self.get_active_feed().filter(*filters).order_by(Feed.expires)
        if limit:
            query = query.limit(limit)
        yield from query

    def list_fetchable(self, limit=0):
        now, feeds = utc_now(), list(self.list_late(limit))
        if feeds:
            for feed in feeds:
                if feed.last_retrieved == UNIX_START:
                    continue
                FEED_LATENESS.labels(feed_type=feed.feed_type.value)\
                        .observe((now - feed.last_retrieved).total_seconds())
            self.update({'id__in': [feed.id for feed in feeds]},
                        {'last_retrieved': now})
        return feeds

    @staticmethod
    def _ensure_icon(attrs):
        if not attrs.get('icon_url'):
            return
        icon_contr = IconController()
        if not icon_contr.read(url=attrs['icon_url']).first():
            icon_contr.create(url=attrs['icon_url'])

    def __clean_feed_fields(self, attrs):
        if attrs.get('category_id') == 0:
            attrs['category_id'] = None
        if self.user_id and attrs.get('category_id'):
            from jarr.controllers import CategoryController
            category = CategoryController().get(id=attrs['category_id'])
            if category.user_id != self.user_id:
                raise Forbidden()
        if 'filters' in attrs:
            attrs['filters'] = [filter_ for filter_ in (attrs['filters'] or [])
                                if isinstance(filter_, dict)]

    def create(self, **attrs):
        self._ensure_icon(attrs)
        self.__clean_feed_fields(attrs)
        return super().create(**attrs)

    def __denorm_cat_id_on_articles(self, feed, attrs):
        if 'category_id' in attrs:
            self.__actrl.update({'feed_id': feed.id},
                                {'category_id': attrs['category_id']})

    def __denorm_title_on_clusters(self, feed, attrs):
        if 'title' in attrs:
            where_clause = [Article.feed_id == feed.id,
                            Article.id == Cluster.main_article_id]
            if self.user_id:
                where_clause.extend([Cluster.user_id == self.user_id])
            session.query(Cluster).filter(*where_clause).update(
                {Cluster.main_feed_title: attrs['title']},
                synchronize_session=False)

    def __update_default_expires(self, feed, attrs):
        now = utc_now()
        min_delta = timedelta(seconds=conf.feed.min_expires)
        max_delta = timedelta(seconds=conf.feed.max_expires)
        min_expires = now + min_delta
        max_expires = now + max_delta
        method = 'from header'
        feed_type = getattr(feed.feed_type, 'value', '')
        if attrs['expires'] is None:
            attrs['expires'] = max_expires
            method = 'defaulted to max'
        try:
            if not isinstance(attrs['expires'], datetime):
                attrs['expires'] = dateutil.parser.parse(attrs['expires'])
            if not attrs['expires'].tzinfo:
                method = 'from header added tzinfo'
                attrs['expires'] = attrs['expires'].replace(
                        tzinfo=timezone.utc)
            elif max_expires < attrs['expires']:
                method = 'from header max limited'
                attrs['expires'] = max_expires
                logger.debug("%r expiring too late, forcing expire in %ds",
                             feed, conf.feed.max_expires)
            elif attrs['expires'] < min_expires:
                method = 'from header min limited'
                attrs['expires'] = min_expires
                logger.debug("%r expiring too early, forcing expire in %ds",
                             feed, conf.feed.min_expires)
        except Exception:
            attrs['expires'] = max_expires
            method = 'defaulted to max'

        art_count = self.__actrl.read(feed_id=feed.id,
            retrieved_date__gt=now - max_delta * SPAN_FACTOR).count()
        if not art_count and method == 'from header min limited':
            attrs['expires'] = now + 2 * min_delta
            method = 'no article, twice min time'
        elif art_count:
            proposed_expires = now + max_delta / art_count / SPAN_FACTOR
            if min_expires < proposed_expires < attrs['expires']:
                attrs['expires'] = proposed_expires
                method = 'computed'
            if proposed_expires < min_expires:
                method = 'many articles, set to min expire'
                attrs['expires'] = min_expires
        exp_s = (attrs['expires'] - now).total_seconds()
        logger.info('%r : %d articles, expiring in %ds (%s)',
                    feed, art_count, exp_s, method)
        FEED_EXPIRES.labels(method=method, feed_type=feed_type).observe(exp_s)

    def update(self, filters, attrs, return_objs=False, commit=True):
        self._ensure_icon(attrs)
        self.__clean_feed_fields(attrs)
        stuff_to_denorm = bool({'title', 'category_id'}.intersection(attrs))
        updating_expires = 'expires' in attrs

        if stuff_to_denorm or updating_expires:
            for feed in self.read(**filters):
                if stuff_to_denorm:
                    self.__denorm_cat_id_on_articles(feed, attrs)
                    self.__denorm_title_on_clusters(feed, attrs)
                if updating_expires:
                    self.__update_default_expires(feed, attrs)
        return super().update(filters, attrs, return_objs, commit)

    def delete(self, obj_id, commit=True):
        from jarr.controllers.cluster import ClusterController
        feed = self.get(id=obj_id)
        logger.debug('DELETE %r - Found feed', feed)
        clu_ctrl = ClusterController(self.user_id)

        logger.info('DELETE %r - removing back ref from cluster to article',
                    feed)
        art_ids = self.__actrl.read(feed_id=obj_id
                                    ).with_entities(self.__actrl._db_cls.id)
        clu_ctrl.update({'user_id': feed.user_id,
                         'main_article_id__in': art_ids},
                        {'main_article_id': None})

        def select_art(col):
            return select([col]).where(Cluster.id == Article.cluster_id,
                                       Article.user_id == feed.user_id)\
                                .order_by(Article.date.asc()).limit(1)

        logger.info('DELETE %r - removing articles', feed)
        session.execute(delete(Article).where(
            Article.feed_id == feed.id,
            Article.user_id == feed.user_id))

        logger.info('DELETE %r - fixing cluster without main article', feed)
        clu_ctrl.update({'user_id': feed.user_id, 'main_article_id': None},
                {'main_title': select_art(Article.title),
                 'main_article_id': select_art(Article.id),
                 'main_feed_title': select([Feed.title])
                                    .where(Cluster.id == Article.cluster_id,
                                           Article.user_id == feed.user_id,
                                           Feed.id == Article.feed_id,
                                           Feed.user_id == feed.user_id)
                                    .order_by(Article.date.asc()).limit(1)})

        logger.info('DELETE %r - removing clusters without main article', feed)
        session.execute(delete(Cluster).where(
            Cluster.user_id == feed.user_id,
            Cluster.main_article_id.__eq__(None)))
        return super().delete(obj_id)

    def update_unread_count(self, feed_id, return_count=False):
        where = tuple()
        if self.user_id:
            where = (Cluster.user_id == self.user_id,
                     Article.user_id == self.user_id)
        unread = session.query(func.count(Article.id))\
            .join(Cluster, and_(Article.cluster_id == Cluster.id,
                                Cluster.user_id == Article.user_id,
                                Cluster.read.__eq__(False), *where)
                  ).filter(Article.feed_id == feed_id)
        if return_count:
            unread = unread.first()[0]
        self.update({'id': feed_id}, {'unread_count': unread})
        if return_count:
            return unread

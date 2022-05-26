import logging
from collections import defaultdict

from sqlalchemy import Integer, and_, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import aliased
from sqlalchemy.sql import exists, select

from jarr.bootstrap import session
from jarr.controllers.article import ArticleController, FeedController
from jarr.controllers.article_clusterizer import Clusterizer
from jarr.lib.filter import process_filters
from jarr.metrics import WORKER_BATCH
from jarr.models import Article, Cluster, Feed

from .abstract import AbstractController

logger = logging.getLogger(__name__)
# static values for join_read
__returned_keys = ('main_title', 'id', 'liked', 'read', 'main_article_id',
                   'main_feed_title', 'main_date', 'main_link')
JR_FIELDS = {key: getattr(Cluster, key) for key in __returned_keys}
JR_SQLA_FIELDS = [getattr(Cluster, key) for key in __returned_keys]
JR_PAGE_LENGTH = 30


class ClusterController(AbstractController):
    _db_cls = Cluster

    # Clusterizer EP
    def clusterize_pending_articles(self):
        results = []
        actrl = ArticleController(self.user_id)
        art_count = actrl.read(cluster_id=None).count()
        logger.info('User(%s) got %d articles to clusterize',
                    self.user_id, art_count)
        WORKER_BATCH.labels(worker_type='clusterizer').observe(art_count)
        clusterizer = Clusterizer(self.user_id)
        feed_ids, fctrl = set(), FeedController(self.user_id)
        for article in actrl.read(cluster_id=None):
            filter_result = process_filters(article.feed.filters,
                                            {'tags': article.tags,
                                             'title': article.title,
                                             'link': article.link})
            result = clusterizer.main(article, filter_result).id
            results.append(result)
            feed_ids.add(article.feed_id)
        for feed_id in feed_ids:
            fctrl.update_unread_count(feed_id)
        return results

    def update(self, filters, attrs, return_objs=False, commit=True):
        if 'read' in attrs:
            fctrl = FeedController(self.user_id)
            if attrs['read']:
                fctrl.decrease_unread_count(self._to_filters(**filters))
            else:
                fctrl.increase_unread_count(self._to_filters(**filters))
        return super().update(filters, attrs, return_objs, commit)

    # UI methods

    def _preprocess_per_article_filters(self, filters):
        """Removing filters aimed at articles and transform them into filters
        for clusters"""
        art_filters = {}
        for key in {'__or__', 'title__ilike', 'content__ilike'}\
                .intersection(filters):
            art_filters[key] = filters.pop(key)

        if art_filters:
            actrl = ArticleController(self.user_id)
            filters['id__in'] = {
                line[0] for line in
                actrl.read(**art_filters).with_entities(Article.cluster_id)}

    @staticmethod
    def _get_selected(fields, art_f_alias, art_c_alias):
        """Return selected fields"""
        selected_fields = list(fields.values())
        selected_fields.append(func.array_agg(
            art_f_alias.feed_id, type_=ARRAY(Integer)).label('feeds_id'))
        return selected_fields

    def _join_on_exist(self, query, alias, attr, value, filters):
        val_col = getattr(alias, attr)
        exist_query = exists(
            select([val_col])
            .where(and_(alias.cluster_id == Cluster.id,
                        alias.user_id == self.user_id, val_col == value))
            .correlate(Cluster).limit(1))
        return query.join(alias, and_(alias.user_id == self.user_id,
                                      alias.cluster_id == Cluster.id,
                                      *filters))\
                    .filter(exist_query)

    @staticmethod
    def _iter_on_query(query):
        """For a given query will iter on it, transforming raw rows to proper
        dictionnaries and handling the agreggation around feeds_id.
        """

        def _ensure_zero_list(clu, key):
            return [i or 0 for i in getattr(clu, key, [])] or [0]

        for clu in query:
            row = {}
            for key in JR_FIELDS:
                row[key] = getattr(clu, key)
            row['feeds_id'] = clu.feeds_id
            yield row

    def join_read(self, feed_id=None, limit=JR_PAGE_LENGTH, **filters):
        filter_on_cat = 'category_id' in filters
        cat_id = filters.pop('category_id', None)
        if self.user_id:
            filters['user_id'] = self.user_id

        self._preprocess_per_article_filters(filters)
        if 'id__in' in filters and not filters['id__in']:
            # filtering by article but did not found anything
            return

        processed_filters = self._to_filters(**filters)

        art_feed_alias, art_cat_alias = aliased(Article), aliased(Article)
        # DESC of what's going on below :
        # base query with the above fields and the aggregations
        query = session.query(
            *self._get_selected(JR_FIELDS, art_feed_alias, art_cat_alias))

        # adding parent filter, but we can't just filter on one id, because
        # we'll miss all the other parent of the cluster
        if feed_id:
            query = self._join_on_exist(query, art_feed_alias,
                                        'feed_id', feed_id, processed_filters)

        elif filter_on_cat:
            # joining only if filtering on categories to lighten the query
            # as every article doesn't obligatorily have a category > outerjoin
            query = self._join_on_exist(query, art_cat_alias,
                                        'category_id', cat_id,
                                        processed_filters)
        if not feed_id:
            query = query.join(art_feed_alias,
                               and_(art_feed_alias.user_id == self.user_id,
                                    art_feed_alias.cluster_id == Cluster.id,
                                    *processed_filters))

        # applying common filter (read / liked)
        # grouping all the fields so that agreg works on distant ids
        yield from self._iter_on_query(
                query.group_by(*JR_SQLA_FIELDS).filter(*processed_filters)
                     .order_by(Cluster.main_date.desc())
                     .limit(limit))

    def delete(self, obj_id, delete_articles=True):
        # handling unread count
        fctrl = FeedController(self.user_id)
        fctrl.decrease_unread_count(self._to_filters(**{'id': obj_id})

        self.update({'id': obj_id}, {'main_article_id': None}, commit=False)
        actrl = ArticleController(self.user_id)
        if delete_articles:
            for art in actrl.read(cluster_id=obj_id):
                actrl.delete_only_article(art, commit=False)
        else:
            actrl.update({'cluster_id': obj_id},
                         {'cluster_id': None,
                          'cluster_reason': None,
                          'cluster_score': None,
                          'cluster_tfidf_with': None,
                          'cluster_tfidf_neighbor_size': None})
        return super().delete(obj_id)

    #
    # Real controllers stuff here
    #

    def count_by_feed(self, **filters):
        return self._count_by(Article.feed_id, **filters)

    def count_by_category(self, **filters):
        return self._count_by(Article.category_id, **filters)

    def _count_by(self, group_on, **filters):
        if self.user_id:
            filters['user_id'] = self.user_id
        return dict(session.query(group_on, func.count(Article.cluster_id))
                           .outerjoin(Cluster,
                                      Article.cluster_id == Cluster.id)
                           .filter(*self._to_filters(**filters))
                           .group_by(group_on).all())

    def get_unreads(self):
        counters = defaultdict(int)
        fctrl = FeedController(self.user_id)
        query = session.query(Feed.category_id, Feed.id, Feed.unread_count,
                              ).where(Feed.user_id == self.user_id)
        for cid, fid, unread in query:
            counters[f"feed-{fid}"] = unread or 0
            if counters[f"feed-{fid}"] < 0:
                counters[f"feed-{fid}"] = fctrl.update_unread_count(
                    fid, return_count=True)
            if cid:
                counters[f"categ-{cid}"] += counters[f"feed-{fid}"]
        return counters

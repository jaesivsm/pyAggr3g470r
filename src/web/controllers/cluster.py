import logging
from datetime import timedelta

from sqlalchemy import Integer, and_, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import aliased
from sqlalchemy.sql import exists, select
from werkzeug.exceptions import NotFound

from bootstrap import SQLITE_ENGINE, db
from web.controllers.article import ArticleController
from web.models import Article, Cluster

from .abstract import AbstractController
from lib.clustering_af.grouper import get_best_match_and_score

logger = logging.getLogger(__name__)


class ClusterController(AbstractController):
    _db_cls = Cluster
    max_day_dist = timedelta(days=7)

    def _get_cluster_by_link(self, article):
        return self.read(user_id=article.user_id,
                         main_date__lt=article.date + self.max_day_dist,
                         main_date__gt=article.date - self.max_day_dist,
                         main_link=article.link).first()

    def _get_cluster_by_title(self, article):
        match = ArticleController(self.user_id).read(
                date__lt=article.date + self.max_day_dist,
                date__gt=article.date - self.max_day_dist,
                user_id=article.user_id,
                category_id=article.category_id,
                title__ilike=article.title).first()
        if match:
            return match.cluster

    def _get_cluster_by_similarity(self, article,
            min_sample_size=10, min_score=0.45):
        if not article.lang:
            return
        art_contr = ArticleController(self.user_id)
        if '_' in article.lang:
            lang_cond = {'lang__like': '%s%%' % article.lang.split('_')[0]}
        else:
            lang_cond = {'lang__like': '%s%%' % article.lang}

        neighbors = list(art_contr.read(
                category_id=article.category_id, user_id=article.user_id,
                date__lt=article.date + self.max_day_dist,
                date__gt=article.date - self.max_day_dist,
                # article isn't this one, and already in a cluster
                cluster_id__ne=None, id__ne=article.id,
                # article is matchable
                valuable_tokens__ne=[], **lang_cond))

        if len(neighbors) < min_sample_size:
            logger.info('only %d docs against %d required, no TFIDF for %r',
                        len(neighbors), min_sample_size, article)
            return

        best_match, score = get_best_match_and_score(article, neighbors)
        if score > min_score:
            return best_match.cluster

    def _create_from_article(self, article,
                             cluster_read=None, cluster_liked=False):
        cluster = Cluster()
        cluster.user_id = article.user_id
        cluster.main_link = article.link
        cluster.main_date = article.date
        cluster.main_feed_title = article.feed.title
        cluster.main_title = article.title
        cluster.main_article_id = article.id
        cluster.read = bool(cluster_read)
        cluster.liked = cluster_liked
        self._enrich_cluster(cluster, article, cluster_read, cluster_liked)

    def _enrich_cluster(self, cluster, article,
                        cluster_read=None, cluster_liked=False,
                        force_article_as_main=False):
        article.cluster = cluster
        # a cluster
        if cluster_read is not None:
            cluster.read = cluster.read and cluster_read
        # once one article is liked the cluster is liked
        cluster.liked = cluster.liked or cluster_liked
        if cluster.main_date > article.date or force_article_as_main:
            cluster.main_title = article.title
            cluster.main_date = article.date
            cluster.main_feed_title = article.feed.title
            cluster.main_article_id = article.id
        db.session.add(cluster)
        db.session.add(article)
        db.session.commit()

    def clusterize(self, article, cluster_read=None, cluster_liked=False):
        """Will add given article to a fitting cluster or create a cluster
        fitting that article."""
        cluster = self._get_cluster_by_link(article)
        if not cluster and getattr(article.category, 'cluster_on_title', None):
            cluster = self._get_cluster_by_title(article)
            if not cluster:
                cluster = self._get_cluster_by_similarity(article)
        if cluster:
            return self._enrich_cluster(cluster, article,
                                        cluster_read, cluster_liked)
        return self._create_from_article(article, cluster_read, cluster_liked)

    def _preprocess_per_article_filters(self, filters):
        art_filters = {}
        for key in {'__or__', 'title__ilike', 'content__ilike'}\
                   .intersection(filters):
            art_filters[key] = filters.pop(key)

        if art_filters:
            art_contr = ArticleController(self.user_id)
            filters['id__in'] = {line[0] for line in art_contr
                    .read(**art_filters).with_entities(Article.cluster_id)}

    @staticmethod
    def _get_selected(fields, art_f_alias, art_c_alias, filter_on_category):
        selected_fields = list(fields.values())
        if SQLITE_ENGINE:
            selected_fields.append(func.group_concat(
                    art_f_alias.feed_id).label('feeds_id'))
            if filter_on_category:
                selected_fields.append(func.group_concat(
                        art_c_alias.category_id).label('categories_id'))
        else:  # pragma: no cover
            selected_fields.append(func.array_agg(art_f_alias.feed_id,
                    type_=ARRAY(Integer)).label('feeds_id'))
            if filter_on_category:
                selected_fields.append(func.array_agg(
                        art_c_alias.category_id,
                        type_=ARRAY(Integer)).label('categories_id'))
        return selected_fields

    def _join_on_exist(self, query, alias, attr, value, filters):
        val_col = getattr(alias, attr)
        exist_query = exists(select([val_col])
                .where(and_(alias.cluster_id == Cluster.id,
                            alias.user_id == self.user_id, val_col == value))
                .correlate(Cluster).limit(1))
        return query.join(alias, and_(alias.user_id == self.user_id,
                                      alias.cluster_id == Cluster.id,
                                      *filters))\
                    .filter(exist_query)

    @staticmethod
    def _iter_on_query(query, fields, filter_on_category):
        for clu in query.order_by(Cluster.main_date.desc()).limit(1000):
            row = {}
            for key in fields:
                row[key] = getattr(clu, key)
            if SQLITE_ENGINE:
                row['feeds_id'] = set(map(int, clu.feeds_id.split(',')))
                if filter_on_category and clu.categories_id:
                    row['categories_id'] = set(
                            map(int, clu.categories_id.split(',')))
                elif filter_on_category:
                    row['categories_id'] = [0]
            else:  # pragma: no cover
                row['feeds_id'] = set(clu.feeds_id)
                if filter_on_category:
                    row['categories_id'] = {i or 0 for i in clu.categories_id}
            yield row

    def join_read(self, feed_id=None, **filters):
        filter_on_cat = 'category_id' in filters
        cat_id = filters.pop('category_id', None)
        if self.user_id:
            filters['user_id'] = self.user_id

        self._preprocess_per_article_filters(filters)
        if 'id__in' in filters and not filters['id__in']:
            # filtering by article but did not found anything
            return

        processed_filters = self._to_filters(**filters)

        returned_keys = ('main_title', 'id', 'liked', 'read',
                'main_article_id', 'main_feed_title', 'main_date', 'main_link')
        fields = {key: getattr(Cluster, key) for key in returned_keys}
        sqla_fields = [getattr(Cluster, key) for key in returned_keys]
        art_feed_alias, art_cat_alias = aliased(Article), aliased(Article)
        # DESC of what's going on below :
        # base query with the above fields and the aggregations
        query = db.session.query(*self._get_selected(fields,
                art_feed_alias, art_cat_alias, filter_on_cat))

        # adding parent filter, but we can't just filter on one id, because
        # we'll miss all the other parent of the cluster
        if feed_id:
            query = self._join_on_exist(query, art_feed_alias,
                                        'feed_id', feed_id, processed_filters)
        else:
            query = query.join(art_feed_alias,
                               and_(art_feed_alias.user_id == self.user_id,
                                    art_feed_alias.cluster_id == Cluster.id,
                                    *processed_filters))
        if filter_on_cat:
            # joining only if filtering on categories to lighten the query
            # as every article doesn't obligatorily have a category > outerjoin
            query = self._join_on_exist(query, art_cat_alias,
                                        'category_id', cat_id,
                                        processed_filters)

        # applying common filter (read / liked)
        # grouping all the fields so that agreg works on distant ids
        yield from self._iter_on_query(query.group_by(*sqla_fields)
                .filter(*processed_filters), fields, filter_on_cat)

    def delete(self, obj_id):
        from web.controllers import ArticleController
        self.update({'id': obj_id}, {'main_article_id': None}, commit=False)
        ArticleController(self.user_id).read(cluster_id=obj_id).delete()
        return super().delete(obj_id)

    @classmethod
    def _extra_columns(cls, role, right):
        return {'articles': {'type': list}}

    def count_by_feed(self, **filters):
        return self._count_by(Article.feed_id, **filters)

    def count_by_category(self, **filters):
        return self._count_by(Article.category_id, **filters)

    def _count_by(self, group_on, **filters):
        if self.user_id:
            filters['user_id'] = self.user_id
        return dict(db.session.query(group_on, func.count(Article.cluster_id))
                              .outerjoin(Cluster,
                                         Article.cluster_id == Cluster.id)
                              .filter(*self._to_filters(**filters))
                              .group_by(group_on).all())

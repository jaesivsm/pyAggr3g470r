import logging
from collections import defaultdict
from datetime import timedelta
from functools import partial

from jarr.bootstrap import conf, session
from jarr.controllers import ArticleController
from jarr.lib.clustering_af.grouper import get_best_match_and_score
from jarr.lib.enums import ArticleType, ClusterReason, ReadReason
from jarr.metrics import ARTICLE_CREATION, TFIDF_SCORE, WORKER_BATCH
from jarr.models import Article, Cluster, Feed
from jarr.signals import event
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)
NO_CLUSTER_TYPE = {ArticleType.image, ArticleType.video, ArticleType.embedded}
WAKABLE_REASONS = {
    ReadReason.marked,
    ReadReason.mass_marked,
    ReadReason.filtered,
}
cluster_event = partial(event.send, module=__name__)


def get_tfidf_pref(feed, pref_name):
    """Tool to figure out clustering setting for a feed.

    For a given feed and a given attribute name will return a boolean
    If this same attribute is set to false on feed's user false will be
    returned, if it's set to false on feed's category false will also be
    returned. If not the value be returned from feed configuration.
    Defaults are set in configurations
    """
    objs = feed.user, feed.category, feed
    for obj in objs:
        if obj is None:
            continue
        if not obj.cluster_conf or pref_name not in obj.cluster_conf:
            continue
        if not obj.cluster_conf[pref_name] and obj is not feed:
            continue
        return obj.cluster_conf.get(pref_name)
    return getattr(conf.clustering.tfidf, pref_name)


def _true_or_unset(attr):
    return or_(attr.__eq__(True), attr.__eq__(None))


class Clusterizer:
    def __init__(self, user_id=None):
        self.user_id = user_id
        self.corpus = []
        self.corpus_initialized = False
        self._config_cache = defaultdict(lambda: defaultdict(dict))

    def get_config(self, obj, attr):
        """For an object among Category, Feed, Cluster and Article a given
        attribute name, will determine config value.
        The attribute will be tested on the given object, and if not either
        True or False, the function will browse parent object to determine
        config value.
        In any case, computed value is cached in Clusterizer instance.
        """

        def cache(val):
            self._config_cache[obj.__class__.__name__][attr][obj.id] = val
            return val

        if obj.id in self._config_cache[obj.__class__.__name__]:
            return self._config_cache[obj.__class__.__name__][obj.id]
        if obj.__class__.__name__ == "Article":
            return cache(self.get_config(obj.feed, attr))
        if obj.__class__.__name__ == "Cluster":
            return cache(
                all(self.get_config(article, attr) for article in obj.articles)
            )
        val = getattr(obj, attr)
        if val is not None:
            logger.debug("%r.%s is %r", obj, attr, val)
            return cache(val)
        if obj.__class__.__name__ == "Feed" and obj.category_id:
            return cache(self.get_config(obj.category, attr))
        return cache(self.get_config(obj.user, attr))

    def add_to_corpus(self, article):
        "Add a given article to the Clusterizer.corpus if article is eligible."
        self.corpus_initialized = True
        if article.article_type not in NO_CLUSTER_TYPE:
            self.corpus.append(article)

    def get_neighbors(self, article):
        """Yield every eligible article eligibe for clustering with a given
        article from the Clusterizer.corpus. If the corpus isn't initialized
        yet, it'll be pulled out of the database.
        """
        if not self.corpus_initialized:
            filters = {
                "__and__": [{"vector__ne": None}, {"vector__ne": ""}],
                "article_type": None,
            }
            self.corpus_initialized = True
            self.corpus = list(
                self._get_query_for_clustering(
                    article, filters=filters, filter_tfidf=True
                )
            )
        tfidf_conf = conf.clustering.tfidf
        low_bound = article.simple_vector_magnitude / tfidf_conf.size_factor
        high_bound = article.simple_vector_magnitude * tfidf_conf.size_factor
        low_bound = max(tfidf_conf.min_vector_size, low_bound)
        for candidate in self.corpus:
            if low_bound <= candidate.simple_vector_magnitude <= high_bound:
                yield candidate

    def _get_cluster_by_link(self, article):
        for candidate in self._get_query_for_clustering(
            article, {"link_hash": article.link_hash}
        ):
            article.cluster_reason = ClusterReason.link
            cluster_event(context="link", result="match", level=logging.INFO)
            return candidate.cluster

    def _get_cluster_by_similarity(self, article):
        neighbors = list(self.get_neighbors(article))

        min_sample_size = get_tfidf_pref(article.feed, "min_sample_size")
        if len(neighbors) < min_sample_size:
            logger.info(
                "only %d docs against %d required, no TFIDF for %r",
                len(neighbors),
                min_sample_size,
                article,
            )
            cluster_event(context="tfidf", result="sample size forbird")
            return None
        logger.info(
            "%r TFIDF is gonna work with a corpus of %d documents",
            article.feed,
            len(neighbors),
        )
        WORKER_BATCH.labels(worker_type="tfidf_batch").observe(len(neighbors))

        best_match, score = get_best_match_and_score(article, neighbors)
        labeled = TFIDF_SCORE.labels(feed_type=article.feed.feed_type.value)
        labeled.observe(score)
        if score > get_tfidf_pref(article.feed, "min_score"):
            article.cluster_reason = ClusterReason.tf_idf
            article.cluster_score = int(score * 1000)
            article.cluster_tfidf_neighbor_size = len(neighbors)
            article.cluster_tfidf_with = best_match.id
            cluster_event(context="tfidf", result="match", level=logging.INFO)
            return best_match.cluster
        cluster_event(context="tfidf", result="miss")

    def _get_query_for_clustering(self, article, filters, filter_tfidf=False):
        time_delta = timedelta(days=conf.clustering.time_delta)
        date_cond = {
            "date__lt": article.date + time_delta,
            "date__gt": article.date - time_delta,
        }
        retr_cond = {
            "retrieved_date__lt": article.retrieved_date + time_delta,
            "retrieved_date__gt": article.retrieved_date - time_delta,
        }
        filters["cluster_id__ne"] = None
        filters["user_id"] = article.user_id
        filters["id__ne"] = article.id
        filters["__or__"] = [date_cond, retr_cond]
        if article.category_id and not self.get_config(
            article, "cluster_same_category"
        ):
            filters["category_id__ne"] = article.category_id
        if not self.get_config(article, "cluster_same_feed"):
            filters["feed_id__ne"] = article.feed_id

        feed_join = [
            Feed.id == Article.feed_id,
            _true_or_unset(Feed.cluster_enabled),
        ]

        if filter_tfidf:
            feed_join.append(_true_or_unset(Feed.cluster_tfidf_enabled))

        query = (
            ArticleController(article.user_id)
            .read(**filters)
            .join(Feed, and_(*feed_join))
        )

        # operations involving categories are complicated, handling in software
        for candidate in query:
            if not self.get_config(candidate, "cluster_enabled"):
                continue
            tfidf_enabled = self.get_config(candidate, "cluster_tfidf_enabled")
            if filter_tfidf and not tfidf_enabled:
                continue
            yield candidate

    def _create_from_article(
        self, article, cluster_read=None, cluster_liked=False
    ):
        cluster = Cluster(user_id=article.user_id)
        article.cluster_reason = ClusterReason.original
        return self.enrich_cluster(
            cluster,
            article,
            cluster_read,
            cluster_liked,
            force_article_as_main=True,
        )

    def enrich_cluster(
        self,
        cluster,
        article,
        cluster_read=None,
        cluster_liked=False,
        force_article_as_main=False,
    ):
        "Will add given article to given cluster."
        article.cluster = cluster
        # handling read status
        if cluster.read is None:  # no read status, new cluster
            cluster.read = bool(cluster_read)
        elif cluster_read is not None:  # filters indicate a read status
            cluster.read = cluster.read and cluster_read
            cluster.read_reason = ReadReason.filtered
            logger.debug("marking as read because of filter %r", cluster)
        elif (
            cluster.read  # waking up a cluster
            and cluster.read_reason in WAKABLE_REASONS
            and self.get_config(article, "cluster_wake_up")
            and self.get_config(cluster, "cluster_wake_up")
        ):
            cluster.read = False
            logger.debug("waking up %r", cluster)
        # once one article is liked the cluster is liked
        cluster.liked = cluster.liked or cluster_liked
        if (
            force_article_as_main
            or cluster.main_date > article.date
            or (
                not article.feed.truncated_content
                and all(
                    cluster_article.feed.truncated_content
                    for cluster_article in cluster.articles
                )
            )
        ):
            cluster.main_title = article.title
            cluster.main_date = article.date
            cluster.main_link = article.link
            cluster.main_feed_title = article.feed.title
            cluster.main_article_id = article.id
        cluster.content = article.content_generator.generate_and_merge(
            cluster.content
        )
        self.add_to_corpus(article)
        session.add(cluster)
        session.add(article)
        session.commit()
        read_reason = cluster.read_reason.value if cluster.read_reason else ""
        ARTICLE_CREATION.labels(
            read_reason=read_reason,
            read="read" if cluster.read else "unread",
            cluster=article.cluster_reason.value,
        ).inc()
        return cluster

    def main(self, article, filter_result=None):
        """Will add given article to a fitting cluster or create a cluster
        fitting that article."""
        filter_result = filter_result or {}
        allow_clustering = filter_result.get("clustering", True)
        filter_read = filter_result.get("read", False)
        filter_liked = filter_result.get("liked", False)
        logger.info("%r - processed filter: %r", article, filter_result)
        cluster_config = self.get_config(article.feed, "cluster_enabled")

        # fetching article so that vector comparison is made on full content
        ArticleController(article.user_id).enhance(article)

        if not allow_clustering:
            cluster_event(context="clustering", result="filter forbid")
        elif not cluster_config:
            cluster_event(context="clustering", result="config forbid")
        else:
            cluster = self._get_cluster_by_link(article)
            if not cluster:
                if not self.get_config(article.feed, "cluster_tfidf_enabled"):
                    cluster_event(context="tfidf", result="config forbid")
                elif article.article_type in NO_CLUSTER_TYPE:
                    cluster_event(context="tfidf", result="wrong article type")
                else:
                    cluster = self._get_cluster_by_similarity(article)
            if cluster:
                return self.enrich_cluster(
                    cluster, article, filter_read, filter_liked
                )
        return self._create_from_article(article, filter_read, filter_liked)

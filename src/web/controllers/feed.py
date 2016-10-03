import logging
from datetime import datetime, timedelta

from bootstrap import conf
from .abstract import AbstractController
from .icon import IconController
from web.models import User, Feed

logger = logging.getLogger(__name__)
DEFAULT_LIMIT = 5


class FeedController(AbstractController):
    _db_cls = Feed

    def __get_art_contr(self):
        from .article import ArticleController
        return ArticleController(self.user_id)

    def list_late(self, delta, max_error=conf.FEED_ERROR_MAX,
                  limit=DEFAULT_LIMIT):
        """Will list either late feed (which have been retrieved for the last
        time sooner than now minus the delta (default to 1h)) or the feed with
        articles recentrly created (later than now minus a quarter the delta
        (default to 15 logically)).

        The idea is to keep very active feed up to date and to avoid missing
        articles du to high activity (when, for example, the feed only displays
        its 30 last entries and produces more than one per minutes).

        Feeds of inactive (not connected for more than a month) or manually
        desactivated users are ignored.
        """
        tenth = delta / 10
        feed_last_retrieved = datetime.utcnow() - delta
        art_last_retr = datetime.utcnow() - (2 * tenth)
        last_conn_max = datetime.utcnow() - timedelta(days=30)
        min_wait = datetime.utcnow() - tenth
        ac = self.__get_art_contr()
        new_art_feed = (ac.read(retrieved_date__gt=art_last_retr,
                                retrieved_date__lt=min_wait)
                          .with_entities(ac._db_cls.feed_id)
                          .distinct())

        query = (self.read(error_count__lt=max_error, enabled=True,
                           __or__=[{'last_retrieved__lt': feed_last_retrieved},
                                   {'last_retrieved__lt': min_wait,
                                    'id__in': new_art_feed}])
                     .join(User).filter(User.is_active.__eq__(True),
                                        User.last_connection >= last_conn_max)
                     .order_by(Feed.last_retrieved))
        if limit:
            query = query.limit(limit)
        yield from query

    def list_fetchable(self, max_error=conf.FEED_ERROR_MAX,
            limit=DEFAULT_LIMIT, refresh_rate=conf.FEED_REFRESH_RATE):
        now, delta = datetime.utcnow(), timedelta(minutes=refresh_rate)
        feeds = list(self.list_late(delta, max_error, limit))
        if feeds:
            self.update({'id__in': [feed.id for feed in feeds]},
                        {'last_retrieved': now})
        return feeds

    def get_inactives(self, nb_days):
        today = datetime.utcnow()
        inactives = []
        for feed in self.read():
            try:
                last_post = feed.articles[0].date
            except IndexError:
                continue
            elapsed = today - last_post
            if elapsed > timedelta(days=nb_days):
                inactives.append((feed, elapsed))
        inactives.sort(key=lambda tup: tup[1], reverse=True)
        return inactives

    def count_by_category(self, **filters):
        return self._count_by(Feed.category_id, filters)

    def _ensure_icon(self, attrs):
        if not attrs.get('icon_url'):
            return
        icon_contr = IconController()
        if not icon_contr.read(url=attrs['icon_url']).count():
            icon_contr.create(**{'url': attrs['icon_url']})

    def __clean_feed_fields(self, attrs):
        if attrs.get('category_id') == 0:
            attrs['category_id'] = None
        if 'filters' in attrs:
            attrs['filters'] = [filter_ for filter_ in attrs['filters']
                                if type(filter_) is dict]

    def create(self, **attrs):
        self._ensure_icon(attrs)
        self.__clean_feed_fields(attrs)
        return super().create(**attrs)

    def update(self, filters, attrs, *args, **kwargs):
        self._ensure_icon(attrs)
        self.__clean_feed_fields(attrs)
        if 'category_id' in attrs:
            for feed in self.read(**filters):
                self.__get_art_contr().update({'feed_id': feed.id},
                        {'category_id': attrs['category_id']})
        return super().update(filters, attrs, *args, **kwargs)

import logging
from typing import Optional, Type

from jarr.bootstrap import conf
from jarr.controllers import ArticleController, FeedController
from jarr.crawler.article_builders.classic import ClassicArticleBuilder
from jarr.crawler.article_builders.abstract import AbstractArticleBuilder
from jarr.crawler.lib.headers_handling import (extract_feed_info,
                                               prepare_headers)
from jarr.crawler.requests_utils import (response_calculated_etag_match,
                                         response_etag_match)
from jarr.lib.enums import FeedType
from jarr.lib.utils import jarr_get, utc_now
from jarr.metrics import FEED_FETCH

logger = logging.getLogger(__name__)


class AbstractCrawler:
    feed_type: Optional[FeedType] = None
    article_builder: Type[AbstractArticleBuilder] = ClassicArticleBuilder

    @classmethod
    def browse_subcls(cls, to_browse=None):
        to_browse = to_browse or cls
        if to_browse.feed_type is not None:
            yield to_browse
        for subcls in to_browse.__subclasses__():
            yield from cls.browse_subcls(subcls)

    def __init__(self, feed):
        self.feed = feed
        self.constructed_feed = {}

    def _metric_fetch(self, result, level=logging.INFO):
        logger.log(level, '%r: responded with %s', self.feed, result)
        FEED_FETCH.labels(feed_type=self.feed.feed_type.value,
                          result=result).inc()

    def set_feed_error(self, error=None, parsed_feed=None):
        error_count = self.feed.error_count + 1
        if error:
            last_error = str(error)
        elif parsed_feed:
            last_error = str(parsed_feed.get('bozo_exception', ''))
        if self.feed.error_count > conf.feed.error_threshold:
            level = logging.WARNING
        else:
            level = logging.DEBUG
        logger.log(level, "%r: fetching feed error'd; error count -> %r",
                   self.feed, error_count)
        logger.debug("%r: last error details %r", self.feed, last_error)
        now = utc_now()
        info = {'error_count': error_count, 'last_error': last_error,
                'user_id': self.feed.user_id, 'last_retrieved': now,
                'expires': None}  # forcing compute by controller

        FEED_FETCH.labels(feed_type=self.feed.feed_type.value,
                          result='error').inc()
        return FeedController().update({'id': self.feed.id}, info)

    def clean_feed(self, response, **info):
        """Will reset the errors counters on a feed that have known errors"""
        now = utc_now()
        info.update({'error_count': 0, 'last_error': None,
                     'last_retrieved': now, 'expires': None})
        info.update(extract_feed_info(response.headers, response.text))

        feed_permanently_redirected = response.history \
            and self.feed.link != response.url \
            and any(r.status_code in {301, 308} for r in response.history)
        if feed_permanently_redirected:
            logger.warning('%r: feed moved from %r to %r', self.feed,
                           self.feed.link, response.url)
            info['link'] = response.url
        if self.constructed_feed.get('icon_url') \
                and self.constructed_feed['icon_url'] != self.feed.icon_url:
            info['icon_url'] = self.constructed_feed['icon_url']
        FeedController(self.feed.user_id).update({'id': self.feed.id}, info)

    def parse_feed_response(self, response):
        raise NotImplementedError()

    def create_missing_article(self, response):
        logger.info('%r: cache validation failed, challenging entries',
                    self.feed)
        parsed = self.parse_feed_response(response)
        if parsed is None:
            return

        ids, entries, skipped_list = [], {}, []
        for entry in parsed['entries']:
            if not entry:
                continue
            builder = self.article_builder(self.feed, entry, parsed)
            if builder.do_skip_creation:
                skipped_list.append(builder.entry_ids)
                logger.debug('%r: skipping article', self.feed)
                continue
            entry_ids = builder.entry_ids
            entries[tuple(sorted(entry_ids.items()))] = builder
            ids.append(entry_ids)
        if not ids and skipped_list:
            logger.debug('%r: nothing to add (skipped %r) %r',
                         self.feed, skipped_list, parsed)
            return
        logger.debug("%r: found %d entries %r", self.feed, len(ids), ids)

        article_created = False
        actrl = ArticleController(self.feed.user_id)
        new_entries_ids = list(actrl.challenge(ids=ids))
        logger.debug("%r: %d entries wern't matched and will be created",
                     self.feed, len(new_entries_ids))
        for id_to_create in new_entries_ids:
            article_created = True
            builder = entries[tuple(sorted(id_to_create.items()))]
            for new_article in builder.enhance():
                article = actrl.create(**new_article)
            logger.info('%r: created %r', self.feed, article)

        if not article_created:
            logger.info('%r: all article matched in db, adding nothing',
                        self.feed)

    def get_url(self):
        return self.feed.link

    def request(self):
        return jarr_get(self.get_url(),
                        timeout=conf.crawler.timeout,
                        user_agent=conf.crawler.user_agent,
                        headers=prepare_headers(self.feed))

    def is_cache_hit(self, response):
        if response.status_code == 304:
            self._metric_fetch('304', logging.DEBUG)
        elif response.status_code == 226:
            self._metric_fetch('226')
        elif response_etag_match(self.feed, response):
            self._metric_fetch('manual-hash-match', logging.DEBUG)
        elif response_calculated_etag_match(self.feed, response):
            self._metric_fetch('home-made-hash-match', logging.DEBUG)
        else:
            self._metric_fetch('cache-miss')
            return False
        return True

    def crawl(self):
        logger.debug('%r: crawling resources', self.feed)
        try:
            response = self.request()
            response.raise_for_status()
        except Exception as error:
            self.set_feed_error(error=error)
            return

        if not self.is_cache_hit(response):
            try:
                self.create_missing_article(response)
            except Exception as error:
                self.set_feed_error(error=error)
                return
        self.clean_feed(response)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.feed.title})>"

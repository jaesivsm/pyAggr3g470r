import logging

import requests
from requests.exceptions import MissingSchema

from jarr.bootstrap import conf
from jarr.lib.content_generator import YOUTUBE_RE, is_embedded_link
from jarr.lib.enums import ArticleType
from jarr.lib.filter import FiltersAction, process_filters
from jarr.lib.url_cleaners import clean_urls, remove_utm_tags
from jarr.lib.utils import clean_lang, digest, utc_now

logger = logging.getLogger(__name__)


class AbstractArticleBuilder:

    def __init__(self, feed, entry, top_level):
        self.feed = feed
        self.entry = entry
        self.article = {}
        self._top_level = top_level
        self.construct(self.entry)

    @property
    def entry_ids(self):
        return {k: self.article[k] for k in ('entry_id', 'feed_id', 'user_id')}

    @property
    def do_skip_creation(self):
        return process_filters(self.feed.filters, self.article,
                               {FiltersAction.SKIP})['skipped']

    def template_article(self):
        return {'feed_id': self.feed.id,
                'category_id': self.feed.category_id,
                'user_id': self.feed.user_id,
                'order_in_cluster': 0,
                'retrieved_date': utc_now()}

    @staticmethod
    def extract_id(entry):
        raise NotImplementedError()

    @staticmethod
    def extract_date(entry):
        raise NotImplementedError()

    @staticmethod
    def extract_title(entry):
        raise NotImplementedError()

    @staticmethod
    def extract_tags(entry):
        raise NotImplementedError()

    @staticmethod
    def extract_link(entry):
        raise NotImplementedError()

    @staticmethod
    def extract_content(entry):
        raise NotImplementedError()

    @staticmethod
    def extract_lang(entry):
        raise NotImplementedError()

    @staticmethod
    def extract_comments(entry):
        raise NotImplementedError()

    @staticmethod
    def to_hash(link):
        return digest(remove_utm_tags(link), alg='sha1', out='bytes')

    def construct(self, entry):
        self.article = self.template_article()
        if not entry:
            return
        self.article['entry_id'] = self.extract_id(entry)
        try:
            self.article['date'] = self.extract_date(entry)
        except Exception:
            self.article['date'] = utc_now()
        self.article['title'] = self.extract_title(entry)
        self.article['tags'] = self.extract_tags(entry)
        self.article['link'] = self.extract_link(entry)
        self.article['content'] = self.extract_content(entry)
        self.article['lang'] = clean_lang(self.extract_lang(entry))
        self.article['comments'] = self.extract_comments(entry)
        if self.article.get('link'):
            self.article['link_hash'] = self.to_hash(self.article['link'])
            if self.article.get('content'):
                self.article['content'] = clean_urls(self.article['content'],
                                                     self.article['link'])

    @classmethod
    def _head(cls, url, reraise=False):
        try:
            headers = {'User-Agent': conf.crawler.user_agent}
            head = requests.head(url, headers=headers, allow_redirects=True,
                                 timeout=conf.crawler.timeout)
            head.raise_for_status()
            return head
        except MissingSchema:
            if reraise:
                raise
            for scheme in 'https:', 'https://', 'http:', 'http://':
                try:
                    return cls._head(scheme + url, reraise=True)
                except Exception as error:
                    logger.debug('got %r for url %s%s', error, scheme, url)
                    continue
        except Exception:
            logger.error("couldn't fetch %r", url)

    @staticmethod
    def _feed_content_type(content_type, article):
        content_type = str(content_type or '')
        if content_type.startswith('image/'):
            article['article_type'] = ArticleType.image
        elif content_type.startswith('video/'):
            article['article_type'] = ArticleType.video
        elif content_type.startswith('audio/'):
            article['article_type'] = ArticleType.audio
        elif is_embedded_link(article['link']):
            article['article_type'] = ArticleType.embedded

    def _all_articles(self):
        yield self.article

    def enhance(self):
        if is_embedded_link(self.article['link']):
            self.article['article_type'] = ArticleType.embedded
            try:  # let's not fetch youtube page, avoid consent page redirect
                video_id = YOUTUBE_RE.match(self.article['link']).group(5)
                self.article['link_hash'] = self.to_hash(video_id)
            except IndexError:
                pass
            yield from self._all_articles()
            return
        head = self._head(self.article['link'])
        if not head:
            yield from self._all_articles()
            return

        if self.article['link'] != head.url:
            self.article['link'] = head.url  # fix link in case of redirect
            # removing utm_tags from link_hash, to allow clustering despite em
            clean_link = remove_utm_tags(self.article['link'])
            if clean_link != self.article['link']:
                clean_head = self._head(clean_link)
                if clean_head:
                    self.article['link_hash'] = self.to_hash(clean_head.url)
        self._feed_content_type(head.headers.get('Content-Type'), self.article)

        if not self.article.get('lang') \
                and head.headers.get('Content-Language'):
            # correcting lang from http headers
            lang = head.headers['Content-Language'].split(',')[0]
            self.article['lang'] = lang
        yield from self._all_articles()

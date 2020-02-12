import html
import logging
import re
import urllib

from feedparser import FeedParserDict
from feedparser import parse as fp_parse

from jarr.lib.const import FEED_MIMETYPES
from jarr.lib.html_parsing import (extract_feed_links, extract_icon_url,
                                   extract_opg_prop, extract_title)
from jarr.lib.jarr_types import FeedType
from jarr.utils import jarr_get

logger = logging.getLogger(__name__)
REDDIT_FEED = re.compile(r'^https?://www.reddit.com/r/(\S+)/$')
INSTAGRAM_RE = re.compile(r'^https?://(www.)?instagram.com/([^ \t\n\r\f\v/]+)')
TUMBLR_RE = re.compile(r'^https?://([^ \t\n\r\f\v/]+).tumblr.com/.*$')
SOUNDCLOUD_RE = re.compile(
        r'^https?://(www.)?soundcloud.com/([^ \t\n\r\f\v/]+)')
KOREUS_RE = re.compile(r'^https?://feeds.feedburner.com/Koreus.*$')


class FeedBuilderController:

    def __init__(self, url, parsed_feed=None):
        self.url = self._fix_url(url)
        self.page_response = None
        self.feed_response = None
        self.parsed_feed = parsed_feed

    @staticmethod
    def _fix_url(url):
        split = urllib.parse.urlsplit(url)
        if not split.scheme and not split.netloc:
            return 'http://' + url
        if not split.scheme:
            return 'http:' + url
        return url

    def any_url(self):
        if self.url:
            yield self.url
        for page in self.feed_response, self.page_response:
            if page and page.url:
                yield page.url

    def is_parsed_feed(self):
        if not self.feed_response and not self.parsed_feed:
            return False
        if not self.parsed_feed:
            if not any(mimetype in self.feed_response.headers['Content-Type']
                    for mimetype in FEED_MIMETYPES):
                return False
            self.parsed_feed = fp_parse(self.feed_response.content)
        if not isinstance(self.parsed_feed, FeedParserDict):
            return False
        return self.parsed_feed['entries'] or not self.parsed_feed['bozo']

    def construct_from_xml_feed_content(self):
        if not self.is_parsed_feed():
            return {}
        fp_feed = self.parsed_feed.get('feed') or {}

        result = {'link': self.feed_response.url,
                  'site_link': fp_feed.get('link'),
                  'title': fp_feed.get('title')}
        if self.parsed_feed.get('href'):
            result['link'] = self.parsed_feed.get('href')
        if fp_feed.get('subtitle'):
            result['description'] = fp_feed.get('subtitle')

        # extracting extra links
        rel_to_link = {'self': 'link', 'alternate': 'site_link'}
        for link in fp_feed.get('links') or []:
            if link['rel'] not in rel_to_link:
                logger.info('unknown link type %r', link)
                continue
            if result.get(rel_to_link[link['rel']]):
                logger.debug('%r already field', rel_to_link[link['rel']])
                continue
            result[rel_to_link[link['rel']]] = link['href']

        # extracting description
        if not result.get('description') \
                and (fp_feed.get('subtitle_detail') or {}).get('value'):
            result['description'] = fp_feed['subtitle_detail']['value']
        return {key: value for key, value in result.items() if value}

    def correct_rss_bridge_feed(self, regex, feed_type):
        def extract_id(url):
            try:
                return regex.split(url, 1)[2]
            except Exception:
                return False
        for url in self.any_url():
            if extract_id(url):
                return extract_id(url)

    def parse_webpage(self):
        result = {'site_link': self.page_response.url}
        icon_url = extract_icon_url(self.page_response)
        if icon_url:
            result['icon_url'] = icon_url
        links = list(extract_feed_links(self.page_response))
        if links:
            result['link'] = links[0]
        if len(links) > 1:
            result['links'] = links
        result['title'] = extract_opg_prop(self.page_response,
                                           og_prop='og:site_name')
        if not result['title']:
            result['title'] = extract_title(self.page_response)
        return {key: value for key, value in result.items() if value}

    def construct(self):
        feed = {'feed_type': FeedType.classic,
                'link': self.url}

        self.feed_response = jarr_get(feed['link'])
        # is an XML feed
        if self.is_parsed_feed():
            feed.update(self.construct_from_xml_feed_content())
            if feed.get('site_link'):
                self.page_response = jarr_get(feed['site_link'])
                feed.update(self.parse_webpage())
        else:  # is a regular webpage
            del feed['link']
            self.page_response = self.feed_response
            self.feed_response = None
            feed.update(self.parse_webpage())
            if feed.get('link'):
                self.feed_response = jarr_get(feed['link'])
                feed.update(self.construct_from_xml_feed_content())

        # marking integration feed
        for regex, feed_type in ((REDDIT_FEED, FeedType.reddit),
                                 (TUMBLR_RE, FeedType.tumblr),
                                 (KOREUS_RE, FeedType.koreus)):
            for check_url in self.any_url():
                if regex.match(check_url):
                    logger.info('%r is %s site', check_url, feed_type.value)
                    feed['feed_type'] = feed_type
        if feed['feed_type'] is FeedType.classic:
            for regex, feed_type in ((INSTAGRAM_RE, FeedType.instagram),
                                     (SOUNDCLOUD_RE, FeedType.soundcloud)):
                corrected = self.correct_rss_bridge_feed(regex, feed_type)
                if corrected:
                    feed['link'] = corrected
                    feed['feed_type'] = feed_type
                    break

        # cleaning text field
        for attr in 'title', 'description':
            if feed.get(attr):
                feed[attr] = html.unescape(feed[attr].strip())
        return feed

import html
import logging
import re
import urllib

import feedparser
from jarr.lib.const import FEED_MIMETYPES, GOOGLE_BOT_UA, REQUIRED_JSON_FEED
from jarr.lib.enums import FeedType
from jarr.lib.html_parsing import (extract_feed_links, extract_icon_url,
                                   extract_opg_prop, extract_title)
from jarr.lib.utils import jarr_get
from requests.exceptions import ReadTimeout

SCHEME = r'(?:https?:)?\/\/'
logger = logging.getLogger(__name__)
REDDIT_FEED = re.compile(SCHEME + r'(www.)?reddit.com/r/([\w\-_]+)/?(.*)$')
INSTAGRAM_RE = re.compile(SCHEME + r'(www.)?instagram.com/([^ \t\n\r\f\v/]+)')
TWITTER_RE = re.compile(SCHEME + r'(www.)?twitter.com/([^ \t\n\r\f\v/]+)')
TUMBLR_RE = re.compile(SCHEME + r'([^ \t\n\r\f\v/]+).tumblr.com/.*$')
YOUTUBE_CHANNEL_RE = re.compile(r'((http|https):\/\/)?(www\.)?youtube\.com\/'
                                r'channel\/([a-zA-Z0-9\-]+)')
YOUTUBE_PLAYLIST_RE = re.compile(
        r'((http|https):\/\/)?(www\.)?youtube\.com\/playlist')
YOUTUBE_VIDEO_RE = re.compile(
        r'((http|https):\/\/)?(www\.)?youtube\.com\/watch')

SOUNDCLOUD_RE = re.compile(
        r'^https?://(www.)?soundcloud.com/([^ \t\n\r\f\v/]+)')
KOREUS_RE = re.compile(r'^https?://feeds.feedburner.com/Koreus.*$')
REDDIT_FEED_PATTERN = "https://www.reddit.com/r/%s/.rss"
YOUTUBE_PATTERN = 'https://www.youtube.com/feeds/videos.xml?%s_id=%s'


class FeedBuilderController:

    def __init__(self, url, parsed_feed=None):
        self.url = self._fix_url(url)
        self.page_response = None
        self.feed_response = None
        self.parsed_feed = parsed_feed

    @property
    def feed_response_content_type(self):
        try:
            return self.feed_response.headers['Content-Type']
        except Exception:
            return ''

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

    @property
    def _is_json_feed(self):
        return ('application/feed+json' in self.feed_response_content_type
                or 'application/json' in self.feed_response_content_type)

    def is_parsed_feed(self):
        if not self.feed_response and not self.parsed_feed:
            return False
        if not self.parsed_feed:
            if self._is_json_feed:
                self.parsed_feed = self.feed_response.json()
                if len(REQUIRED_JSON_FEED.intersection(self.parsed_feed)) != 2:
                    return False
            elif any(mimetype in self.feed_response_content_type
                     for mimetype in FEED_MIMETYPES):
                self.parsed_feed = feedparser.parse(self.feed_response.content)
            else:
                return False
        if not isinstance(self.parsed_feed, (feedparser.FeedParserDict, dict)):
            return False
        return (self.parsed_feed.get('entries')
                or self.parsed_feed.get('items')
                or not self.parsed_feed.get('bozo'))

    def construct_from_xml_feed_content(self):
        if not self.is_parsed_feed():
            return {}
        fp_feed = self.parsed_feed.get('feed') or {}

        result = {'link': self.feed_response.url,
                  'site_link': fp_feed.get('href') or fp_feed.get('link'),
                  'title': fp_feed.get('title')}
        if self.parsed_feed.get('href'):
            result['link'] = self.parsed_feed.get('href')
        if fp_feed.get('subtitle'):
            result['description'] = fp_feed.get('subtitle')
        if (fp_feed.get('image') or {}).get('href'):
            result['icon_url'] = fp_feed['image']['href']

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

    def construct_from_json_feed_content(self):
        if not self.is_parsed_feed():
            return {}
        result = {'feed_type': FeedType.json,
                  'site_link': self.parsed_feed.get('home_page_url'),
                  'link': self.feed_response.url,
                  'icon_url': (self.parsed_feed.get('favicon')
                               or self.parsed_feed.get('icon')),
                  'description': self.parsed_feed.get('description'),
                  'title': self.parsed_feed.get('title')}
        try:
            result['links'] = [hub.get('url')
                               for hub in self.parsed_feed.get('hubs', [])]
        except Exception:
            pass
        return {key: value for key, value in result.items() if value}

    def construct_from_feed_content(self):
        if self._is_json_feed:
            return self.construct_from_json_feed_content()
        return self.construct_from_xml_feed_content()

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

    @staticmethod
    def _handle_known_malfunctionning_link(feed):
        # reddit's subs don't automatically provide rss feed
        reddit_match = REDDIT_FEED.match(feed['link'])
        if reddit_match and not reddit_match.group(3):
            feed['link'] = REDDIT_FEED_PATTERN % reddit_match.group(2)
            feed['feed_type'] = FeedType.reddit
            return feed
        youtube_match = YOUTUBE_CHANNEL_RE.match(feed['link'])
        if youtube_match:
            feed['site_link'] = feed['link']
            feed['link'] = YOUTUBE_PATTERN % (
                'channel', youtube_match.group(4))
        if YOUTUBE_VIDEO_RE.match(feed['link']) \
                or YOUTUBE_PLAYLIST_RE.match(feed['link']):
            split = urllib.parse.urlsplit(feed['link'])
            if split.query:
                query = urllib.parse.parse_qs(split.query)
                if query.get('list'):
                    list_id = query['list'][0]
                    feed['site_link'] = feed['link']
                    feed['link'] = YOUTUBE_PATTERN % ('playlist', list_id)
        return feed

    @staticmethod
    def http_get(url):
        try:
            return jarr_get(url)
        except (ReadTimeout, TimeoutError):
            return jarr_get(url, user_agent=GOOGLE_BOT_UA)

    def construct(self):
        feed = {'feed_type': FeedType.classic, 'link': self.url}
        feed = self._handle_known_malfunctionning_link(feed)

        self.feed_response = self.http_get(feed['link'])
        # is an XML feed
        if self.is_parsed_feed():
            feed.update(self.construct_from_feed_content())
            if feed.get('site_link'):
                self.page_response = self.http_get(feed['site_link'])
                feed = dict(self.parse_webpage(), **feed)
        else:  # is a regular webpage
            del feed['link']
            self.page_response = self.feed_response
            self.feed_response = None
            feed = dict(self.parse_webpage(), **feed)
            if feed.get('link'):
                self.feed_response = self.http_get(feed['link'])
                feed.update(self.construct_from_feed_content())

        # marking integration feed
        for regex, feed_type in ((REDDIT_FEED, FeedType.reddit),
                                 (TUMBLR_RE, FeedType.tumblr),
                                 (KOREUS_RE, FeedType.koreus)):
            for check_url in self.any_url():
                if regex.match(check_url):
                    logger.info('%r is %s site', check_url, feed_type.value)
                    feed['feed_type'] = feed_type
                    break
        if feed['feed_type'] in {FeedType.classic, FeedType.json}:
            for regex, feed_type in ((TWITTER_RE, FeedType.twitter),
                                     (INSTAGRAM_RE, FeedType.instagram),
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

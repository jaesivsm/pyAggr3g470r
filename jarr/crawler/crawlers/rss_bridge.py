from typing import Optional
from urllib.parse import SplitResult, urlencode, urlsplit, urlunsplit

from jarr.bootstrap import conf
from jarr.crawler.article_builders.rss_bridge import (
    RSSBridgeArticleBuilder, RSSBridgeTwitterArticleBuilder)
from jarr.crawler.crawlers.classic import ClassicCrawler
from jarr.crawler.lib.headers_handling import prepare_headers
from jarr.lib.enums import FeedType
from jarr.lib.utils import jarr_get


class RssBridgeAbstractCrawler(ClassicCrawler):
    bridge: str
    bridge_format = "AtomFormat"
    article_builder = RSSBridgeArticleBuilder
    feed_type: Optional[FeedType] = None  # forcing this crawler to be ignored

    def request(self):
        return jarr_get(
            self.get_url(),
            timeout=conf.crawler.timeout,
            user_agent=conf.crawler.user_agent,
            headers=prepare_headers(self.feed),
            ssrf_protect=False,
        )

    def get_url(self):
        split = (
            urlsplit(conf.plugins.rss_bridge)
            if conf.plugins.rss_bridge
            else None
        )

        query = {
            "action": "display",
            "format": self.bridge_format,
            "bridge": self.bridge,
            "u": self.feed.link,
        }

        return urlunsplit(
            SplitResult(
                scheme=split.scheme,
                netloc=split.netloc,
                path=split.path or "/",
                query=urlencode(query),
                fragment="",
            )
        )


class InstagramCrawler(RssBridgeAbstractCrawler):
    feed_type = FeedType.instagram
    bridge = "InstagramBridge"


class SoundcloudCrawler(RssBridgeAbstractCrawler):
    feed_type = FeedType.soundcloud
    bridge = "SoundcloudBridge"


class TwitterCrawler(RssBridgeAbstractCrawler):
    feed_type = FeedType.twitter
    bridge = "TwitterBridge"
    article_builder = RSSBridgeTwitterArticleBuilder

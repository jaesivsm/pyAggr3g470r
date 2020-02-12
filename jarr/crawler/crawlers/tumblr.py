import logging

from jarr.bootstrap import conf
from jarr.crawler.crawlers.classic import ClassicCrawler
from jarr.crawler.lib.headers_handling import prepare_headers
from jarr.lib.jarr_types import FeedType
from jarr.lib.utils import jarr_get

logger = logging.getLogger(__name__)


class TumblrCrawler(ClassicCrawler):
    feed_type = FeedType.classic

    def request(self):
        headers = prepare_headers(self.feed)
        # TODO inject tumblr header !
        return jarr_get(self.get_url(),
                        timeout=conf.crawler.timeout,
                        user_agent=conf.crawler.user_agent,
                        headers=headers)

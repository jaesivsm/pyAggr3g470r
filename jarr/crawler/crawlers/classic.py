import logging
from typing import Optional

import feedparser
from jarr.controllers.feed_builder import FeedBuilderController
from jarr.crawler.crawlers.abstract import AbstractCrawler
from jarr.lib.enums import FeedType

logger = logging.getLogger(__name__)


class ClassicCrawler(AbstractCrawler):
    feed_type: Optional[FeedType] = FeedType.classic

    def parse_feed_response(self, response):
        parsed = feedparser.parse(response.content.strip())
        fbc = FeedBuilderController(self.feed.link, parsed)
        if not fbc.is_parsed_feed():
            self.set_feed_error(parsed_feed=parsed)
            return
        self.constructed_feed.update(fbc.construct_from_xml_feed_content())
        return parsed

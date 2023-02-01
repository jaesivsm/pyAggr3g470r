from jarr.controllers.feed_builder import FeedBuilderController
from jarr.crawler.article_builders.json import JsonArticleBuilder
from jarr.crawler.crawlers.abstract import AbstractCrawler
from jarr.lib.enums import FeedType


class JSONCrawler(AbstractCrawler):
    feed_type = FeedType.json
    article_builder = JsonArticleBuilder

    def parse_feed_response(self, response):
        parsed = response.json()
        parsed['entries'] = parsed.pop('items')
        fbc = FeedBuilderController(self.feed.link, parsed)
        if not fbc.is_parsed_feed():
            self.set_feed_error(parsed_feed=parsed)
            return
        self.constructed_feed.update(fbc.construct_from_xml_feed_content())
        return parsed

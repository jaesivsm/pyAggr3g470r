import json
import logging
import unittest

from mock import Mock, patch

from jarr.bootstrap import conf
from jarr.controllers import ArticleController, FeedController
from jarr.crawler.crawlers.classic import ClassicCrawler
from jarr.crawler.main import clusterizer, process_feed
from jarr.crawler.requests_utils import (response_calculated_etag_match,
                                         response_etag_match)
from jarr.lib.enums import FeedType
from jarr.lib.const import UNIX_START
from jarr.lib.utils import digest
from jarr.models.feed import Feed
from tests.base import JarrFlaskCommon

logger = logging.getLogger('jarr')
BASE_COUNT = 36


def crawler():
    user_ids = set()
    for feed in FeedController().list_fetchable(limit=1):
        process_feed.apply(args=[feed.id])
        user_ids.add(feed.user_id)
    for user_id in user_ids:
        clusterizer.apply(args=[user_id])


class CrawlerTest(JarrFlaskCommon):
    feed_path = 'tests/fixtures/example.feed.atom'

    def setUp(self):
        super().setUp()
        with open(self.feed_path, encoding='utf8') as fd:
            self._content = fd.read()
        self._is_secure_served \
            = patch('jarr.lib.url_cleaners.is_secure_served')
        self._p_req = patch('jarr.crawler.crawlers.abstract.jarr_get')
        self._p_con = patch('jarr.crawler.crawlers.classic.FeedBuilderControl'
                            'ler.construct_from_xml_feed_content')
        self.is_secure_served = self._is_secure_served.start()
        self.jarr_req = self._p_req.start()
        self.jarr_con = self._p_con.start()

        self.is_secure_served.return_value = True
        self.resp_status_code = 200
        self.resp_headers = {}
        self.resp_raise = None

        def _api_req(url, **kwargs):
            if url.startswith('feed') and len(url) == 6:
                resp = Mock(status_code=self.resp_status_code,
                            headers=self.resp_headers, history=[],
                            content=self._content, text=self._content)
                resp.raise_for_status.return_value = self.resp_raise
                resp.json = lambda: json.loads(self._content)
                return resp

            url = url.split(conf.api_root)[1].strip('/')
            kwargs.pop('allow_redirects', None)
            kwargs.pop('params', None)
            kwargs.pop('json', None)
            if 'auth' in kwargs:
                kwargs['user'] = kwargs['auth'][0]
                del kwargs['auth']
            response = self._api('get', url, **kwargs)
            response.raise_for_status = Mock()
            return response

        self.jarr_con.return_value = {}
        self.jarr_req.side_effect = _api_req

    def tearDown(self):
        self._is_secure_served.stop()
        self._p_req.stop()
        self._p_con.stop()
        super().tearDown()

    @staticmethod
    def _reset_feeds_freshness(**kwargs):
        if 'expires' not in kwargs:
            kwargs['expires'] = UNIX_START
        if 'last_retrieved' not in kwargs:
            kwargs['last_retrieved'] = UNIX_START
        if 'etag' not in kwargs:
            kwargs['etag'] = ''
        if 'last_modified' not in kwargs:
            kwargs['last_modified'] = ''
        FeedController().update({}, kwargs)

    def test_http_crawler_add_articles(self):
        self.assertEqual(BASE_COUNT, ArticleController().read().count())

        crawler()
        articles = list(ArticleController().read())
        new_count = len(articles)
        self.assertNotEqual(BASE_COUNT, new_count)
        self.assertTrue(BASE_COUNT < new_count)

        for art in articles:
            self.assertFalse('srcset=' in art.content)
            self.assertFalse('src="/' in art.content)

        self.resp_status_code = 304
        crawler()
        self.assertEqual(new_count, ArticleController().read().count())

    def test_no_add_on_304(self):
        self.resp_status_code = 304
        self.assertEqual(BASE_COUNT, ArticleController().read().count())
        crawler()
        self.assertEqual(BASE_COUNT, ArticleController().read().count())

    def test_no_add_feed_skip(self):
        self.resp_status_code = 304
        self.assertEqual(BASE_COUNT, ArticleController().read().count())
        crawler()
        FeedController().update({}, {'filters': [{"type": "tag contains",
                                                  "action on": "match",
                                                  "pattern": "pattern5",
                                                  "action": "skipped"},
                                                 {"type": "simple match",
                                                  "action on": "match",
                                                  "pattern": "pattern5",
                                                  "action": "mark as read"},
                                                 {"type": "regex",
                                                  "action on": "match",
                                                  "pattern": "pattern5",
                                                  "action": "skipped"}]})

        crawler()
        self.assertEqual(BASE_COUNT, ArticleController().read().count())

    def test_matching_etag(self):
        self._reset_feeds_freshness(etag='fake etag')
        self.resp_headers = {'etag': 'fake etag'}
        self.assertEqual(BASE_COUNT, ArticleController().read().count())

        crawler()

        self.assertEqual(BASE_COUNT, ArticleController().read().count())
        self._reset_feeds_freshness(etag=f"jarr/\"{digest(self._content)}\"")
        self.resp_headers = {'etag': f"jarr/\"{digest(self._content)}\""}

        crawler()
        self.assertEqual(BASE_COUNT, ArticleController().read().count())

        self._reset_feeds_freshness(etag='jarr/fake etag')
        self.resp_headers = {'etag': '########################'}

        crawler()
        self.assertNotEqual(BASE_COUNT, ArticleController().read().count())


class JsonCrawlerTest(CrawlerTest):
    feed_path = 'tests/fixtures/feed.json'

    def setUp(self):
        super().setUp()
        self.resp_headers = {'content-type': 'application/json'}
        FeedController().update({}, {'feed_type': 'json'})


class CrawlerMethodsTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.feed = Feed(user_id=1, id=1, title='title',
                         description='description', etag='', error_count=5,
                         feed_type=FeedType.classic, link='link')
        self.resp = Mock(text='text', headers={}, status_code=304, history=[])

    def test_etag_matching_w_constructed_etag(self):
        self.feed.etag = f"jarr/\"{digest('text')}\""
        self.assertFalse(response_etag_match(self.feed, self.resp))
        self.assertTrue(response_calculated_etag_match(self.feed, self.resp))

    def test_etag_no_matching_wo_etag(self):
        self.feed.etag = ''
        self.assertFalse(response_etag_match(self.feed, self.resp))
        self.assertFalse(response_calculated_etag_match(self.feed, self.resp))

    def test_etag_matching(self):
        self.resp.headers['etag'] = self.feed.etag = 'etag'
        self.assertTrue(response_etag_match(self.feed, self.resp))
        self.assertFalse(response_calculated_etag_match(self.feed, self.resp))

    @patch('jarr.crawler.main.FeedController.update')
    def test_set_feed_error_w_error(self, fctrl_update):
        original_error_count = self.feed.error_count
        ClassicCrawler(self.feed).set_feed_error(Exception('an error'))

        fctrl_update.assert_called_once()
        filters, data = fctrl_update.mock_calls[0][1]
        self.assertEqual(filters['id'], self.feed.id)
        self.assertEqual(original_error_count + 1, data['error_count'])
        self.assertEqual('an error', data['last_error'])

    @patch('jarr.crawler.main.FeedController.update')
    def test_set_feed_error_w_parsed(self, fctrl_update):
        original_error_count = self.feed.error_count
        ClassicCrawler(self.feed).set_feed_error(
                parsed_feed={'bozo_exception': 'an error'})

        fctrl_update.assert_called_once()
        filters, data = fctrl_update.mock_calls[0][1]
        self.assertEqual(filters['id'], self.feed.id)
        self.assertEqual(original_error_count + 1, data['error_count'])
        self.assertEqual('an error', data['last_error'])

    @patch('jarr.crawler.main.FeedController.update')
    def test_clean_feed(self, fctrl_update):
        ClassicCrawler(self.feed).clean_feed(self.resp)
        fctrl_update.assert_called_once()
        filters, data = fctrl_update.mock_calls[0][1]

        self.assertEqual(filters['id'], self.feed.id)
        self.assertTrue('link' not in data)
        self.assertTrue('title' not in data)
        self.assertTrue('description' not in data)
        self.assertTrue('site_link' not in data)
        self.assertTrue('icon_url' not in data)

    @patch('jarr.crawler.main.FeedController.update')
    def test_clean_feed_update_link(self, fctrl_update):
        self.resp.history.append(Mock(status_code=301))
        self.resp.url = 'new_link'
        ClassicCrawler(self.feed).clean_feed(self.resp)

        fctrl_update.assert_called_once()
        filters, data = fctrl_update.mock_calls[0][1]
        self.assertEqual(filters['id'], self.feed.id)
        self.assertEqual('new_link', data['link'])
        self.assertTrue('title' not in data)
        self.assertTrue('description' not in data)
        self.assertTrue('site_link' not in data)
        self.assertTrue('icon_url' not in data)

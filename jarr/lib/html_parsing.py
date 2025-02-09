import logging
import urllib
from functools import lru_cache

from bs4 import BeautifulSoup, SoupStrainer

from jarr.bootstrap import conf
from jarr.lib.const import FEED_MIMETYPES
from jarr.lib.utils import jarr_get, rebuild_url

logger = logging.getLogger(__name__)
CHARSET_TAG = b"<meta charset="


def try_get_icon_url(url, *splits):
    for split in splits:
        if split is None:
            continue
        rb_url = rebuild_url(url, split)
        response = None
        # if html in content-type, we assume it's a fancy 404 page
        try:
            response = jarr_get(
                rb_url, conf.crawler.timeout, conf.crawler.user_agent
            )
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
        except Exception:
            logger.exception("something went wrong while fetching %r", rb_url)
        else:
            if response.ok and "html" not in content_type and response.content:
                return response.url
    return None


def _meta_w_charset(elem):
    return elem.name == "meta" and "charset" in elem.attrs


def _extract_charset(content, strainer):
    soup = BeautifulSoup(content, "html.parser", parse_only=strainer)
    for meta in soup.find_all(_meta_w_charset):
        return meta.attrs["charset"]


def _try_encodings(content, *encodings):
    for encoding in encodings:
        try:
            return content.decode(encoding)
        except Exception:
            pass
    return content.decode("utf8", "ignore")


@lru_cache(maxsize=None)
def get_soup(content, header_encoding="utf8", head_only=True):
    """Try parsing html content and caching parsed result.

    For a content and an encoding will return a bs4 object which will be
    cached so you can call on this method as often as you want.

    As the encoding written in the HTML is more reliable, ```get_soup``` will
    try this one before parsing with the one in args.
    """
    strainer = SoupStrainer("head") if head_only else None
    decoded_content = None
    if not isinstance(content, str):
        encodings = (
            [_extract_charset(content, strainer), header_encoding]
            if CHARSET_TAG in content
            else [header_encoding]
        )
        decoded_content = _try_encodings(content, encodings)
    for cnt in decoded_content, content:
        if cnt:
            try:
                return BeautifulSoup(cnt, "html.parser", parse_only=strainer)
            except Exception as error:
                logger.warning("something went wrong when parsing: %r", error)


def extract_opg_prop(response, og_prop, all_body=False):
    "From a requests.Response objects will extract an opengraph attribute"
    soup = get_soup(response.content, response.encoding, not all_body)
    try:
        return soup.find("meta", {"property": og_prop}).attrs["content"]
    except Exception:
        pass
    if not all_body:
        return extract_opg_prop(response, og_prop, all_body=True)


def extract_title(response):
    soup = get_soup(response.content, response.encoding)
    title = extract_opg_prop(response, "og:title")
    if title:
        return title
    try:
        return soup.find("title").text
    except Exception:
        pass


def _check_keys(**kwargs):
    """Returns a callable for BeautifulSoup.find_all.

    Will also check existence of keys and values
    they hold in the in listed elements.
    """

    def wrapper(elem):
        for key, vals in kwargs.items():
            if not elem.has_attr(key):
                return False
            if not all(val in elem.attrs[key] for val in vals):
                return False
        return True

    return wrapper


def extract_icon_url(response):
    split = urllib.parse.urlsplit(response.url)
    soup = get_soup(response.content, response.encoding)
    if not soup:
        return
    icons = soup.find_all(_check_keys(rel=["icon", "shortcut"]))
    if not icons:
        icons = soup.find_all(_check_keys(rel=["icon"]))
    if icons:
        for icon in icons:
            icon_url = try_get_icon_url(icon.attrs["href"], split)
            if icon_url:
                return icon_url

    icon_url = try_get_icon_url("/favicon.ico", split)
    if icon_url:
        return icon_url


def extract_feed_links(response, all_body=False):
    yielded = False
    split = urllib.parse.urlsplit(response.url)
    soup = get_soup(response.content, response.encoding, not all_body)
    if soup is not None:
        for tpe in FEED_MIMETYPES:
            for alternate in soup.find_all("link", rel="alternate", type=tpe):
                yield rebuild_url(alternate.attrs["href"], split)
                yielded = True
    if not yielded and not all_body:
        yield from extract_feed_links(response, all_body=True)


def clean_article_content(content) -> str:
    "Remove notion of height, width or positionning in integrated articles"
    forbidden_css = "width", "height", "position"
    forbidden_attrs = "width", "height"
    replace_if_absent = {"img": {"data-src": "src"}}
    cleaned = False
    try:
        soup = get_soup(content, head_only=False)
        for element in soup.find_all(lambda elem: elem.has_attr("style")):
            if any(key in element.attrs["style"] for key in forbidden_css):
                del element.attrs["style"]
                cleaned = True
        for attr in forbidden_attrs:
            for element in soup.find_all(lambda elem: elem.has_attr(attr)):
                del element.attrs[attr]
                cleaned = True
        for tag, attrs in replace_if_absent.items():
            for element in soup.find_all(
                tag, **{key: True for key in attrs.keys()}
            ):
                for find, replace in attrs.items():
                    element.attrs[replace] = element.attrs[find]
                    del element.attrs[find]
                    cleaned = True
    except Exception as error:
        msg = "An error occured while triming forbidden elements from html %r"
        logger.debug(msg, error)
    if cleaned:
        return str(soup)
    return content

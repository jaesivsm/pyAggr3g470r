import logging
import re
import types
import urllib
from datetime import datetime, timezone
from enum import Enum
from hashlib import md5, sha1

import advocate
import requests
from jarr.lib.const import GOOGLE_BOT_UA
from requests.exceptions import SSLError

logger = logging.getLogger(__name__)
RFC_1123_FORMAT = "%a, %d %b %Y %X %Z"
LANG_FORMAT = re.compile("^[a-z]{2}(_[A-Z]{2})?$")
CORRECTABLE_LANG_FORMAT = re.compile("^[A-z]{2}(.[A-z]{2})?.*$")
LANG_FORMAT = re.compile(r"^[a-z]{2}(_[A-Z]{2})?$")
CORRECTABLE_LANG_FORMAT = re.compile(r"^[A-z]{2}(.[A-z]{2})?.*$")
PRIVATE_IP = re.compile(
    r"(^127\.)|(^192\.168\.)|(^10\.)|(^172\.1[6-9]\.)|(^172\.2[0-9]\.)|"
    r"(^172\.3[0-1]\.)|(^::1$)|(^[fF][cCdD])"
)


def utc_now():
    return datetime.utcnow().replace(tzinfo=timezone.utc)


def clean_lang(lang: str):
    if not lang or not isinstance(lang, str):
        return
    if LANG_FORMAT.match(lang):
        return lang
    if not CORRECTABLE_LANG_FORMAT.match(lang):
        return
    proper_lang = lang[0:2].lower()
    if len(lang) >= 5:
        proper_lang = f"{proper_lang}_{lang[3:5].upper()}"
    return proper_lang


def rfc_1123_utc(time_obj=None, delta=None):
    """Return time obj or now formated in the RFC1123 style (with delta)."""
    if time_obj is None:
        time_obj = utc_now()
    if delta is not None:
        time_obj += delta
    return time_obj.strftime(RFC_1123_FORMAT)


def default_handler(obj):
    """JSON handler for default query formatting."""
    if isinstance(obj, (set, frozenset, filter, types.GeneratorType)):
        return list(obj)
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(
        f"Object of type {type(obj)} with value of {obj!r} "
        "is not JSON serializable"
    )


def rebuild_url(url, base_split):
    split = urllib.parse.urlsplit(url)
    if split.scheme and split.netloc:
        return url  # url is fine
    new_split = urllib.parse.SplitResult(
        scheme=split.scheme or base_split.scheme,
        netloc=split.netloc or base_split.netloc,
        path=split.path,
        query=split.query,
        fragment=split.fragment,
    )
    return urllib.parse.urlunsplit(new_split)


def digest(text, alg="md5", out="str", encoding="utf8"):
    method = md5 if alg == "md5" else sha1
    text = text.encode(encoding) if hasattr(text, "encode") else text
    return getattr(method(text), "hexdigest" if out == "str" else "digest")()


def jarr_get(
    url,
    timeout=None,
    user_agent=None,
    headers=None,
    ssrf_protect=True,
    **kwargs,
):
    from jarr.bootstrap import conf  # prevent circular import

    if ssrf_protect:
        http_get = advocate.get
    else:
        http_get = requests.get

    timeout = timeout or conf.crawler.timeout
    user_agent = user_agent or conf.crawler.user_agent
    constructed_headers = {"User-Agent": user_agent}
    if headers is not None:
        constructed_headers.update(headers)
    request_kwargs = {
        "allow_redirects": True,
        "timeout": timeout,
        "headers": constructed_headers,
    }
    request_kwargs.update(kwargs)
    if "youtube.com" in url:
        cookies = request_kwargs.get("cookies") or {}
        cookies["CONSENT"] = "YES+1"
        request_kwargs["cookies"] = cookies
        constructed_headers["User-Agent"] = GOOGLE_BOT_UA
    try:
        return http_get(url, **request_kwargs)
    except SSLError:
        request_kwargs["verify"] = False
        return http_get(url, **request_kwargs)

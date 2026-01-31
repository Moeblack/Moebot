import re
import urllib.parse
from typing import Iterable

import httpx

from ...utils import debug_print

# 常见的 B 站相关域名（用于快速判断与过滤）
_BILIBILI_HOST_KEYWORDS = (
    "bilibili.com",
    "b23.tv",
    "bilivideo.com",
    "bili.tv",
)

# URL 粗略提取（允许参数里有中文/转义等，后续再做过滤）
_URL_RE = re.compile(r"https?://[^\s\]\[\)\(\"\'<>]+", re.IGNORECASE)

# QQ 卡片里的 JSON/XML 经常把分隔符转义成实体：&#44; &amp; 等
# 这里做一个轻量级“预解码”，让 URL 正则能正确提取。
_ENTITY_FIXES = (
    ("&#44;", ","),
    ("&amp;", "&"),
    ("\\/", "/"),
)


def preprocess_card_text(text: str) -> str:
    """预处理 QQ 卡片文本，尽量还原 URL 可解析形态。"""
    if not text:
        return text
    for src, dst in _ENTITY_FIXES:
        text = text.replace(src, dst)
    return text


def _contains_bilibili_host(url: str) -> bool:
    url_l = url.lower()
    return any(k in url_l for k in _BILIBILI_HOST_KEYWORDS)


def extract_urls_from_segments_text(texts: Iterable[str]) -> list[str]:
    """从若干段文本中提取 URL（去重，保持顺序）。"""
    urls: list[str] = []
    seen: set[str] = set()
    for t in texts:
        if not t:
            continue
        t = preprocess_card_text(t)
        for m in _URL_RE.finditer(t):
            u = m.group(0).strip().rstrip(".,;!?)】】》")
            if u and u not in seen:
                urls.append(u)
                seen.add(u)
    return urls


def choose_best_bilibili_url(urls: list[str]) -> str | None:
    """在候选 URL 中挑选一个“最像视频/动态/直播”的主链接。"""
    bilis = [u for u in urls if _contains_bilibili_host(u)]
    if not bilis:
        return None

    # 优先级：视频 > 动态 > 直播 > 短链 > 其他
    def score(u: str) -> int:
        ul = u.lower()
        if "bilibili.com/video/" in ul or "bv" in ul:
            return 100
        if "t.bilibili.com/" in ul or "dynamic" in ul:
            return 90
        if "live.bilibili.com/" in ul:
            return 80
        if "b23.tv/" in ul:
            return 70
        return 10

    return sorted(bilis, key=score, reverse=True)[0]


def is_short_url(url: str) -> bool:
    ul = url.lower()
    return "b23.tv/" in ul or "is.gd/" in ul or "tinyurl.com/" in ul


def _strip_tracking_params(url: str) -> str:
    """尽量去掉 b 站常见追踪参数，让链接更干净。"""
    try:
        parsed = urllib.parse.urlsplit(url)
        qs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        drop_keys = {
            # 常见分享追踪
            "spm_id_from",
            "from_spmid",
            "vd_source",
            "share_source",
            "share_medium",
            "share_plat",
            "share_from",
            "share_session_id",
            "share_tag",
            "timestamp",
            "buvid",
            "mid",
            "plat_id",
            "unique_k",
            "bbid",
            "from",
            "spmid",
            "is_story_h5",
        }
        filtered = [(k, v) for (k, v) in qs if k.lower() not in drop_keys]
        new_q = urllib.parse.urlencode(filtered, doseq=True)
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_q, parsed.fragment))
    except Exception:
        return url


def _try_expand_b23_redirect(url: str) -> str:
    """如果是 b23 短链，尝试通过 HEAD 跳转拿到落地长链接（失败则原样返回）。"""
    if "b23.tv/" not in url.lower():
        return url

    try:
        # b23.tv 的跳转对 UA/证书有时候比较挑，这里尽量兼容。
        with httpx.Client(verify=False, follow_redirects=False, timeout=6) as client:
            r = client.head(url, headers={"User-Agent": "Mozilla/5.0"})
            loc = r.headers.get("Location")
            return loc or url
    except Exception:
        return url


def normalize_bilibili_share_url(url: str) -> str:
    """规范化 B 站分享链接（目前主要针对 b23 短链去追踪参数）。

    设计目标：用户明确表示“不需要转短链”，因此这里不再生成 is.gd/tinyurl。
    """
    return _strip_tracking_params(url)


def shorten_url(url: str) -> str | None:
    """兼容旧接口：输出你想要的最短“BV 直链”形态。

    规则：
    - 如果输入是 b23：先展开一次跳转拿到落地链接
    - 对落地链接：清理追踪参数
    - 如果最终能识别出 BV：固定输出为 https://www.bilibili.com/video/{BV}
    """

    url = normalize_bilibili_share_url(url)
    url = _try_expand_b23_redirect(url)
    url = _strip_tracking_params(url)

    m = re.search(r"/video/(BV[0-9A-Za-z]+)", url)
    if m:
        return f"https://www.bilibili.com/video/{m.group(1)}"

    # 找不到 BV 就退回清理后的链接
    return url

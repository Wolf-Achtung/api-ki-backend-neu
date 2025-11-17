# scripts/rss_healthcheck.py
from __future__ import annotations
import sys, time, json, argparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

def check_feed(url: str, timeout: int = 10) -> dict:
    req = Request(url, headers={"User-Agent": "KI-Status-Report/1.0 (+rss-health)"})
    t0 = time.time()
    try:
        with urlopen(req, timeout=timeout) as r:
            content_type = r.headers.get("Content-Type", "")
            data = r.read(4096)
            ok = r.status == 200 and (b"<rss" in data or b"<feed" in data or b"<rdf" in data)
            return {"url": url, "status": r.status, "content_type": content_type, "ok": ok, "elapsed_ms": int((time.time()-t0)*1000)}
    except HTTPError as e:
        return {"url": url, "status": e.code, "ok": False, "error": str(e)}
    except URLError as e:
        return {"url": url, "status": 0, "ok": False, "error": str(e)}
    except Exception as e:
        return {"url": url, "status": 0, "ok": False, "error": repr(e)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="Path to JSON with list of feeds", default="data/rss_sources_extra.json")
    args = ap.parse_args()
    feeds = []
    with open(args.json, "r", encoding="utf-8") as f:
        obj = json.load(f)
        for grp in obj.values():
            feeds.extend([x["url"] for x in grp])
    results = [check_feed(u) for u in feeds]
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()

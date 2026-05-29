"""Proper ASP.NET AJAX async postback against the agenda calendar."""
import re
from datetime import date
from bs4 import BeautifulSoup
from curl_cffi import requests

UA = "chrome131"
BASE = "https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/"
AGENDA = BASE + "Agenda/Default.aspx"

EPOCH_DATE = date(2026, 5, 1)
EPOCH_ID = 9617


def date_to_id(d: date) -> int:
    return EPOCH_ID + (d - EPOCH_DATE).days


sess = requests.Session(impersonate=UA)
sess.get(BASE + "Search/Default.aspx", timeout=30)
r = sess.get(AGENDA, timeout=30)
soup = BeautifulSoup(r.text, "html.parser")


def hidden(name):
    el = soup.find("input", {"name": name})
    return el.get("value", "") if el else ""


vs = hidden("__VIEWSTATE")
vsg = hidden("__VIEWSTATEGENERATOR")
vsenc = hidden("__VIEWSTATEENCRYPTED")
print(f"  __VIEWSTATE={len(vs)}  GEN={vsg}  ENC={'yes' if vsenc else 'no'}")

# Pick a recent Tuesday — May 12 2026
day_id = date_to_id(date(2026, 5, 12))
print(f"\n  posting back for May 12 2026, day_id={day_id}")

post_data = {
    "ctl00$ScriptManager1": "ctl00$DefaultContent$upLeftTop|ctl00$DefaultContent$agendaCalendar",
    "__EVENTTARGET": "ctl00$DefaultContent$agendaCalendar",
    "__EVENTARGUMENT": str(day_id),
    "__LASTFOCUS": "",
    "__VIEWSTATE": vs,
    "__VIEWSTATEGENERATOR": vsg,
    "__ASYNCPOST": "true",
}
if vsenc:
    post_data["__VIEWSTATEENCRYPTED"] = vsenc

headers = {
    "X-MicrosoftAjax": "Delta=true",
    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
    "Referer": AGENDA,
    "Origin": "https://publicdocs.co.tulare.ca.us",
}

rp = sess.post(AGENDA, data=post_data, headers=headers, timeout=60)
print(f"  status={rp.status_code} bytes={len(rp.content)}")
print(f"  content-type={rp.headers.get('content-type')}")

# Save raw
with open("_questys_ajax_response.txt", "w", encoding="utf-8") as f:
    f.write(rp.text)

# Parse the pipe-delimited UpdatePanel response: len|type|name|payload|len|type|...
print(f"\n  first 800 chars of response:")
print(f"  {rp.text[:800]!r}")

# Look for the UpdatePanel payload format
# Format: <len>|<type>|<controlId>|<content>|<len>|<type>|...
print(f"\n  response chunks (parsed):")
parts = rp.text.split("|")
i = 0
chunk_idx = 0
while i < len(parts) and chunk_idx < 20:
    try:
        clen = int(parts[i])
        ctype = parts[i + 1]
        cname = parts[i + 2]
        if i + 3 + 1 > len(parts):
            break
        content = "|".join(parts[i + 3:])[:clen]
        print(f"    [{chunk_idx}] len={clen:>6}  type={ctype:<20}  name={cname[:40]:<40}  content_head={content[:80]!r}")
        i += 3
        # advance past content (find next sep by length)
        i_consumed = 0
        joined = ""
        while i < len(parts):
            joined += parts[i]
            if len(joined) >= clen:
                break
            joined += "|"
            i += 1
        i += 1
        chunk_idx += 1
    except (ValueError, IndexError):
        break

# Extract File.ashx IDs from response
fids = sorted(set(re.findall(r"File\.ashx\?id=(\d+)", rp.text)))
print(f"\n  File.ashx IDs in response: {len(fids)}  {fids[:20]}")

# Look for iframe src in response
iframe_srcs = re.findall(r"(?:src|location)\s*=\s*['\"]?([^'\";\s]*?(?:Files|Meeting)[\w/.?=&-]*?\.aspx[^'\";\s]*)", rp.text, re.I)
iframe_srcs = sorted(set(iframe_srcs))
print(f"\n  *.aspx URLs (Files/Meeting/iframe): {len(iframe_srcs)}")
for s in iframe_srcs[:5]:
    print(f"    {s}")

from curl_cffi import requests

sess = requests.Session(impersonate="chrome131")
sess.get("https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/Search/Default.aspx", timeout=30)

for did in [2914, 164293, 179269]:
    r = sess.get(f"https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/File.ashx?id={did}&v=1", timeout=30)
    ct = r.headers.get("content-type", "")
    cd = r.headers.get("content-disposition", "")
    print(f"id={did}: status={r.status_code} bytes={len(r.content)} ct={ct} cd={cd[:80]}")
    print(f"  raw: {r.content[:200]!r}")
    print()

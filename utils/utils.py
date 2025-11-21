import re

DATA_URL_RE= re.compile(r"^data:image\/([a-zA-Z0-9.+-]+);base64,",re.IGNORECASE)

def split_data_url(data_url:str):
    m = DATA_URL_RE.match(data_url)
    if m:
        mime = m.group(1).lower() 
        b64 = DATA_URL_RE.sub("", data_url)
        return mime, b64
    if re.fullmatch(r"[A-Za-z0-9+/=\r\n]+", data_url):
        return "jpeg", data_url.strip()
    raise ValueError("Invalid image data url or base64 string")

def size_fromm_b64(b64:str)->int:
    return int(len(b64) *3 / 4)

 
def dedup_and_merge(items):
    acc={}
    for it in items:
        n = it.get("name","")
        if not n: continue
        conf = float(it.get("confidence",0))
        qty= it.get("approx_qty_grams")
        if n in acc:
            acc[n]["confidence"] = max(acc[n]["confidence"],conf)
            if qty is not None:
                acc[n]["approx_qty_grams"] = (acc[n]["approx_qty_grams"] or 0) + float(qty)
                
        else:
            acc[n]= {
                "name":n,
                "confidence":conf
            }
            if qty is not None:
                acc[n]["approx_qty_grams"]= float(qty)
    return list(acc.values())[:20]
        
import hashlib, re
def normalize_template(text):
    text=re.sub(r'(?im)^\s*(?:sample\s*id|样本编号|文档编号)\s*[:：].*$', 'SAMPLE_ID', text)
    text=re.sub(r'https?://\S+|www\.\S+', 'URL', text, flags=re.I)
    text=re.sub(r'[\w.+-]+@[\w.-]+', 'EMAIL', text)
    text=re.sub(r'\d{3,4}[- ]?\d{7,8}', 'PHONE', text)
    text=re.sub(r'\d{1,4}(?:[-/:]\d{1,4})+', 'DATE_TIME', text)
    text=re.sub(r'\d+', 'NUM', text)
    return re.sub(r'\s+', ' ', text).strip()
def template_fingerprint(text):
    return hashlib.sha256(normalize_template(text).encode()).hexdigest()
def ngrams(text, n=5):
    text=normalize_template(text); return {text[i:i+n] for i in range(max(0,len(text)-n+1))}

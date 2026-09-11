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
def character_ngrams(text, n=5):
    text=normalize_template(text); return {text[i:i+n] for i in range(max(0,len(text)-n+1))}
def jaccard_similarity(a,b): return len(a&b)/len(a|b) if a|b else 0.0
def build_template_groups(records,n=5,threshold=.8):
    records=list(records); parent=list(range(len(records)))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    vec=[character_ngrams(r.get('benchmark_text',r.get('text','')),n) for r in records]; pairs=[]
    for i in range(len(records)):
        for j in range(i):
            score=jaccard_similarity(vec[i],vec[j])
            if score>=threshold: union(i,j); pairs.append((j,i,score))
    groups={}
    for i in range(len(records)): groups.setdefault(find(i),[]).append(i)
    return [[records[i] for i in ids] for ids in groups.values()],pairs
ngrams=character_ngrams

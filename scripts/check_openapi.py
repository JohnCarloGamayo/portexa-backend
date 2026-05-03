import requests
url='http://127.0.0.1:8000/openapi.json'
try:
    r=requests.get(url,timeout=5)
    print('STATUS',r.status_code)
    txt=r.text
    print('/api/v1/ai/embed-rag-chat' in txt)
    # print snippet
    i=txt.find('embed-rag-chat')
    if i!=-1:
        print(txt[max(0,i-200):i+200])
except Exception as e:
    print('ERR',e)

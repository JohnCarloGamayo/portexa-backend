const http = require('http');
http.get('http://127.0.0.1:8000/openapi.json', res=>{
  let s='';
  res.on('data',d=>s+=d);
  res.on('end', ()=>{
    console.log('STATUS',res.statusCode);
    console.log(s.indexOf('/api/v1/ai/embed-rag-chat')!==-1);
    const i = s.indexOf('embed-rag-chat');
    if(i!==-1) console.log(s.slice(Math.max(0,i-200), i+200));
  });
}).on('error', e=>{ console.error('ERR',e.message) });

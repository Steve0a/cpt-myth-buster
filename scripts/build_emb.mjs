import fs from 'fs';import {pipeline} from '@huggingface/transformers';
// Rebuild kb_emb.json whenever FAQ/MYTHS change. Usage: node build_emb.mjs <site_dir>
const dir=process.argv[2];const h=fs.readFileSync(dir+'/index.html','utf8');const js=h.split('<script>')[1].split('</script>')[0];
const data=js.slice(js.indexOf('const CATS='),js.indexOf('function srcHTML'));const {MYTHS,FAQ}=new Function('esc',data+';return {MYTHS,FAQ};')(s=>s);
const KB=[...FAQ.map(x=>({q:x[0],a:x[1].replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim()})),...MYTHS.map(x=>({q:x[0],a:x[1]}))];
const M='Xenova/bge-small-en-v1.5';const ex=await pipeline('feature-extraction',M,{dtype:'q8'});
const emb=async a=>(await ex(a,{pooling:'cls',normalize:true})).tolist().map(v=>v.map(x=>+x.toFixed(4)));
fs.writeFileSync(dir+'/kb_emb.json',JSON.stringify({model:M,prefix:'Represent this sentence for searching relevant passages: ',pooling:'cls',count:KB.length,q:await emb(KB.map(k=>k.q)),qa:await emb(KB.map(k=>k.q+'. '+k.a))}));
console.log('built',KB.length);

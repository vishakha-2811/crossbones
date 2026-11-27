import json
from renderer import number_entries

TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>Crossbones</title>
<style>
body{font-family:Georgia,'Times New Roman',serif;margin:20px;min-height:100vh;color:#d9d0bb;
 background:radial-gradient(ellipse at 50% -10%,#3a0a0e 0%,#0a0708 60%,#000 100%)}
h1{margin:0;display:flex;align-items:center;gap:14px;font-size:42px;color:#e8dfc8;
 letter-spacing:6px;text-transform:uppercase;text-shadow:0 0 14px #b3121b,0 2px 0 #000}
h1 svg{filter:drop-shadow(0 0 6px #b3121b)}
.sub{color:#9a8f78;margin:6px 0 18px;font-style:italic;letter-spacing:1px;
 border-left:3px solid #b3121b;padding-left:10px}
.wrap{display:flex;gap:32px;flex-wrap:wrap;align-items:flex-start}
#gridbox{overflow:auto;max-width:100%;padding:12px;background:#0f0b0b;
 border:2px solid #3b1a1a;border-radius:4px;box-shadow:0 0 24px #b3121b44,inset 0 0 20px #000}
table{border-collapse:collapse}
td{width:30px;height:30px;padding:0;position:relative}
td.on input{width:100%;height:100%;box-sizing:border-box;border:1px solid #5a4a3a;text-align:center;
 font:bold 16px 'Courier New',monospace;padding:0;background:#e8dfc8;color:#1a1210;text-transform:uppercase}
td.on input.hl{background:#d9b98a}
td.on input.good{background:#9fbf8a}
td.on input.bad{background:#d65a5a;color:#fff}
td.on input:focus{outline:2px solid #b3121b;background:#f4ead2}
.n{position:absolute;top:0;left:2px;font-size:9px;color:#6a1016;font-weight:bold;pointer-events:none}
.clues{max-width:560px}
.clue{padding:5px 8px;cursor:pointer;border-radius:2px;border-left:2px solid transparent}
.clue:hover,.clue.sel{background:#2a0e11;border-left-color:#b3121b}
.origin{color:#c9473f;font-family:'Courier New',monospace;font-size:12px;margin-top:2px}
button{margin:0 6px 12px 0;padding:7px 14px;border:1px solid #b3121b;border-radius:2px;
 background:#1a0809;color:#e8dfc8;font-family:Georgia,serif;letter-spacing:1px;
 text-transform:uppercase;font-size:12px;cursor:pointer}
button:hover{background:#b3121b;color:#fff;box-shadow:0 0 10px #b3121b}
h3{margin:16px 0 4px;color:#b3121b;letter-spacing:4px;text-transform:uppercase;
 border-bottom:1px solid #3b1a1a;padding-bottom:4px}
</style></head><body>
<h1><svg width="56" height="56" viewBox="0 0 64 64"><g fill="#e8dfc8"><g transform="rotate(45 32 32)"><rect x="6" y="28" width="52" height="8" rx="4"/><circle cx="8" cy="26" r="6"/><circle cx="8" cy="38" r="6"/><circle cx="56" cy="26" r="6"/><circle cx="56" cy="38" r="6"/></g><g transform="rotate(-45 32 32)"><rect x="6" y="28" width="52" height="8" rx="4"/><circle cx="8" cy="26" r="6"/><circle cx="8" cy="38" r="6"/><circle cx="56" cy="26" r="6"/><circle cx="56" cy="38" r="6"/></g></g></svg>Crossbones</h1>
<div class="sub">Dig up the code. Every answer is a verified symbol. Nothing here is a ghost.</div>
<button onclick="check()">Judge</button>
<button onclick="revealWord()">Exhume word</button>
<button onclick="revealAll()">Dig up all</button>
<button onclick="clearAll()">Bury</button>
<div class="wrap">
 <div id="gridbox"><table id="grid"></table></div>
 <div class="clues"><h3>Across</h3><div id="across"></div><h3>Down</h3><div id="down"></div></div>
</div>
<script>
const D=__DATA__;
const key=(r,c)=>r+','+c;
const cellsOf=e=>{const a=[];for(let i=0;i<e.len;i++)a.push(e.dir==='across'?key(e.r,e.c+i):key(e.r+i,e.c));return a;};
const inputs={},numAt={};
D.entries.forEach(e=>{numAt[key(e.r,e.c)]=e.n;});
const on=new Set(D.cells.map(c=>key(c[0],c[1])));
let active=null,last=null;

function entriesAt(k){return D.entries.filter(e=>cellsOf(e).includes(k));}
function highlight(){
  Object.values(inputs).forEach(i=>i.classList.remove('hl'));
  if(active)cellsOf(active).forEach(k=>inputs[k].classList.add('hl'));
  document.querySelectorAll('.clue').forEach(d=>d.classList.toggle('sel',active&&+d.dataset.i===D.entries.indexOf(active)));
}
function focusCell(k){inputs[k].focus();}
function advance(k,step){
  if(!active)return;
  const ks=cellsOf(active),j=ks.indexOf(k)+step;
  if(j>=0&&j<ks.length)focusCell(ks[j]);
}
function show(i){document.getElementById('o'+i).hidden=false;}

const gridEl=document.getElementById('grid');
for(let r=0;r<D.h;r++){
  const tr=document.createElement('tr');
  for(let c=0;c<D.w;c++){
    const td=document.createElement('td'),k=key(r,c);
    if(on.has(k)){
      td.className='on';
      if(numAt[k]){const s=document.createElement('span');s.className='n';s.textContent=numAt[k];td.appendChild(s);}
      const inp=document.createElement('input');inp.maxLength=1;inputs[k]=inp;
      inp.addEventListener('focus',()=>{
        const here=entriesAt(k);
        if(!active||!cellsOf(active).includes(k))active=here.find(e=>active&&e.dir===active.dir)||here[0];
        highlight();
      });
      inp.addEventListener('click',()=>{
        const here=entriesAt(k);
        if(last===k&&here.length>1)active=here.find(e=>e!==active);
        last=k;highlight();
      });
      inp.addEventListener('input',()=>{
        inp.value=inp.value.replace(/[^a-z]/gi,'').toUpperCase();
        inp.classList.remove('good','bad');
        if(inp.value)advance(k,1);
      });
      inp.addEventListener('keydown',ev=>{
        if(ev.key==='Backspace'&&!inp.value)advance(k,-1);
      });
      td.appendChild(inp);
    }
    tr.appendChild(td);
  }
  gridEl.appendChild(tr);
}

D.entries.map((e,i)=>({e,i})).sort((a,b)=>a.e.n-b.e.n).forEach(({e,i})=>{
  const d=document.createElement('div');d.className='clue';d.dataset.i=i;
  d.innerHTML='<b>'+e.n+'.</b> ';
  d.appendChild(document.createTextNode(e.clue));
  const o=document.createElement('div');o.className='origin';o.id='o'+i;o.hidden=true;
  o.textContent='\u2192 '+e.answer+'  ('+e.origin+')';
  d.appendChild(o);
  d.addEventListener('click',()=>{active=e;highlight();focusCell(cellsOf(e)[0]);});
  document.getElementById(e.dir).appendChild(d);
});

function check(){
  D.entries.forEach((e,i)=>{
    let all=true;
    cellsOf(e).forEach((k,j)=>{
      const inp=inputs[k];inp.classList.remove('good','bad');
      if(inp.value)inp.classList.add(inp.value===e.answer[j]?'good':'bad');
      if(inp.value!==e.answer[j])all=false;
    });
    if(all)show(i);
  });
}
function revealWord(){
  if(!active)return;
  cellsOf(active).forEach((k,j)=>{inputs[k].value=active.answer[j];});
  show(D.entries.indexOf(active));check();
}
function revealAll(){D.entries.forEach((e,i)=>{cellsOf(e).forEach((k,j)=>{inputs[k].value=e.answer[j];});show(i);});check();}
function clearAll(){
  Object.values(inputs).forEach(i=>{i.value='';i.classList.remove('good','bad');});
  D.entries.forEach((e,i)=>{document.getElementById('o'+i).hidden=true;});
}
</script></body></html>"""


def write_html(grid, entries, clues, path="crossword.html"):
    numbers = number_entries(entries)
    rows = [r for r, _ in grid]
    cols = [c for _, c in grid]
    r0, c0 = min(rows), min(cols)
    data = {
        "h": max(rows) - r0 + 1,
        "w": max(cols) - c0 + 1,
        "cells": [[r - r0, c - c0, ch] for (r, c), ch in grid.items()],
        "entries": [{
            "n": numbers[(e.row, e.col)],
            "dir": e.direction,
            "r": e.row - r0,
            "c": e.col - c0,
            "len": len(e.answer),
            "answer": e.answer,
            "clue": clues.get(e.answer, ""),
            "origin": f"{e.file}:{e.line}",
        } for e in entries],
    }
    payload = json.dumps(data).replace("</", "<\\/")
    with open(path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.replace("__DATA__", payload))
    return path
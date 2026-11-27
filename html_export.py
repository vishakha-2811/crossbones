import json
from renderer import number_entries

TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>Crossbones</title>
<style>
body{font-family:system-ui,sans-serif;margin:20px;background:#14121a;color:#eee}
h1{margin:0}.sub{color:#aaa;margin:4px 0 16px}
.wrap{display:flex;gap:32px;flex-wrap:wrap;align-items:flex-start}
#gridbox{overflow:auto;max-width:100%}
table{border-collapse:collapse}
td{width:30px;height:30px;padding:0;position:relative}
td.on input{width:100%;height:100%;box-sizing:border-box;border:1px solid #555;text-align:center;
 font:bold 16px monospace;padding:0;background:#fff;color:#111;text-transform:uppercase}
td.on input.hl{background:#ffe9a8}
td.on input.good{background:#b9f0c0}
td.on input.bad{background:#ffb3b3}
.n{position:absolute;top:0;left:2px;font-size:9px;color:#333;pointer-events:none}
.clues{max-width:560px}
.clue{padding:4px 6px;cursor:pointer;border-radius:4px}
.clue:hover,.clue.sel{background:#2d2840}
.origin{color:#9fe3a8;font-family:monospace;font-size:12px;margin-top:2px}
button{margin:0 6px 12px 0;padding:6px 12px;border:0;border-radius:6px;background:#6c3fd6;color:#fff;cursor:pointer}
h3{margin:14px 0 4px}
</style></head><body>
<h1>Crossbones</h1>
<div class="sub">Solve the puzzle to learn the codebase. Every answer is a verified symbol from the repo.</div>
<button onclick="check()">Check</button>
<button onclick="revealWord()">Reveal word</button>
<button onclick="revealAll()">Reveal all</button>
<button onclick="clearAll()">Clear</button>
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
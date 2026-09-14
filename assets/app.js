let state={
 recipes:[],offers:[],offerStatus:"waiting",view:"today",week:[],
 disliked:new Set(JSON.parse(localStorage.getItem("disliked")||"[]")),
 liked:new Set(JSON.parse(localStorage.getItem("liked")||"[]")),
 checked:new Set(JSON.parse(localStorage.getItem("checked")||"[]")),
 quick:JSON.parse(localStorage.getItem("quick")||"[]"),
 quickStats:JSON.parse(localStorage.getItem("quickStats")||"{}"),
 filter:"Alla"
};
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
const mins=r=>r.minutes??null;
const days=["Måndag","Tisdag","Onsdag","Torsdag","Fredag","Lördag","Söndag"];
const stop=new Set(["och","med","utan","färsk","färska","svensk","svenska","ica","arla","st","g","kg","dl","ml","msk","tsk","port","ca"]);
const canon=s=>String(s||"").toLowerCase().replace(/[,:()]/g," ").replace(/filéer/g,"filé").replace(/kycklingbröst/g,"kycklingfilé").replace(/färsen/g,"färs").replace(/\s+/g," ").trim();
function words(s){return canon(s).split(" ").filter(w=>w.length>=4&&!stop.has(w))}
function offerMatches(r){
 if(state.offerStatus!=="live")return [];
 const hay=canon((r.name||"")+" "+(r.ingredients||[]).join(" "));
 return state.offers.filter(o=>{
   const ws=words(o.name);
   return ws.some(w=>hay.includes(w)) || (hay.includes("köttfärs")&&ws.some(w=>w.includes("färs"))) ||
          (hay.includes("kyckling")&&ws.some(w=>w.includes("kyckling"))) ||
          (hay.includes("korv")&&ws.some(w=>w.includes("korv")));
 }).slice(0,3);
}
function stableJitter(r,i){
 const w=new Date(),week=Math.ceil((((w-new Date(w.getFullYear(),0,1))/86400000)+new Date(w.getFullYear(),0,1).getDay()+1)/7);
 let s=(r.id||r.name)+":"+week+":"+i,h=0;for(let c of s)h=(h*31+c.charCodeAt(0))>>>0;return (h%100)/100;
}
function score(r,i){
 let s=0,m=mins(r),matches=offerMatches(r);
 if(matches.length)s+=35+Math.min(20,(matches.length-1)*10);
 if(state.liked.has(r.name))s+=18;
 if(i<4&&m&&m<=35)s+=12;
 if(r.lunch>=4)s+=6;if(r.freeze>=4)s+=3;
 if((r.tags||[]).includes("barnvänlig"))s+=4;
 if(i===4&&((r.tags||[]).includes("fredag")||/taco|burrito|quesadilla/i.test(r.name)))s+=15;
 if(state.disliked.has(r.name))s-=999;
 return s+stableJitter(r,i)*3;
}
function buildWeek(){
 const used=new Set();state.week=[];
 for(let i=0;i<7;i++){
   let pool=state.recipes.filter(r=>!used.has(r.name)&&!state.disliked.has(r.name));
   if(!pool.length)pool=state.recipes;
   pool=[...pool].sort((a,b)=>score(b,i)-score(a,i));
   let r=pool[0];used.add(r.name);state.week.push({day:days[i],recipe:r});
 }
}
async function init(){
 try{
   const [rr,oo]=await Promise.all([
     fetch("./recipes.json?"+Date.now()).then(r=>r.json()),
     fetch("./offers.json?"+Date.now()).then(r=>r.ok?r.json():({status:"unavailable",offers:[]}))
   ]);
   state.recipes=rr;state.offerStatus=oo.status||"unavailable";state.offers=oo.offers||[];
   buildWeek();render();bindNav();
 }catch(e){$("#view").innerHTML='<div class="card">Kunde inte läsa Matappens data just nu.</div>'}
}
function bindNav(){
 document.querySelectorAll(".nav-btn").forEach(b=>b.onclick=()=>{state.view=b.dataset.view;document.querySelectorAll(".nav-btn").forEach(x=>x.classList.toggle("active",x===b));render();window.scrollTo({top:0,behavior:"smooth"})});
 $("#profileBtn").onclick=showInfo;
}
function meta(r,onHero=false){
 let a=[];if(mins(r))a.push(`⏱ ${mins(r)} min`);
 if(r.external)a.push(`↗ ${r.source}`);
 else{if(r.lunch)a.push(`🥡 Matlåda ${r.lunch}/5`);if(r.freeze)a.push(`❄️ Frys ${r.freeze}/5`)}
 return a.map(x=>`<span class="soft-chip">${esc(x)}</span>`).join("");
}
function offerBadge(r){
 const m=offerMatches(r);if(!m.length)return "";
 const o=m[0];return `<div class="offer">🔥 Vald utifrån ICA-erbjudande: <b>${esc(o.name)}</b>${o.price?` · ${esc(o.price)}`:""}</div>`;
}
function image(r,cls="recipe-image"){return r.image?`<img class="${cls}" src="${esc(r.image)}" alt="" loading="lazy" referrerpolicy="no-referrer">`:""}
function render(){if(state.view==="today")$("#view").innerHTML=todayView();if(state.view==="week")$("#view").innerHTML=weekView();if(state.view==="shop")$("#view").innerHTML=shopView();if(state.view==="recipes")$("#view").innerHTML=recipeView();wire()}
function todayView(){
 const d=new Date().getDay(),idx=d===0?6:d-1,p=state.week[idx],t=state.week[(idx+1)%7];
 const status=state.offerStatus==="live"?`🔥 ${state.offers.length} ICA-erbjudanden inlästa`:"ICA-erbjudanden kunde inte verifieras – veckan byggs utan dem";
 return `<section class="hero-card">${image(p.recipe,"hero-image")}<div class="hero-label">${p.day} · dagens middag</div><div class="hero-title">${esc(p.recipe.name)}</div><div class="meta">${meta(p.recipe,true)}</div>${offerBadge(p.recipe)}<div class="hero-actions"><button class="light" data-recipeid="${esc(p.recipe.id)}">Visa recept</button><button class="ghost" data-swap="${idx}">↻ Byt rätt</button></div></section>
 <div class="status-line ${state.offerStatus==="live"?"ok":"warn"}">${esc(status)}</div>
 <section class="section"><div class="section-head"><h2>Lägg till snabbt</h2><span class="muted">lär sig vad du brukar lägga till</span></div><div class="quick-grid">${smartQuick().map(x=>`<button class="quick" data-add="${esc(x)}">＋ ${esc(x)}<small>${state.quickStats[x]?`tillagd ${state.quickStats[x]} ggr`:"till inköpslistan"}</small></button>`).join("")}</div></section>
 <section class="section"><div class="section-head"><h2>I morgon</h2></div><div class="card mini-meal">${image(t.recipe,"thumb")}<div><div class="day">${t.day}</div><div class="meal">${esc(t.recipe.name)}</div><div class="row">${meta(t.recipe)}</div>${offerBadge(t.recipe)}</div></div></section>`;
}
function smartQuick(){
 const defaults=["Mjölk","Bröd","Ägg","Yoghurt","Diskmedel","Toalettpapper"];
 return [...new Set([...Object.entries(state.quickStats).sort((a,b)=>b[1]-a[1]).map(x=>x[0]),...defaults])].slice(0,4);
}
function weekView(){
 return `<section class="section" style="margin-top:4px"><div class="section-head"><div><h2>Veckans middagar</h2><div class="muted">${state.offerStatus==="live"?"Prioriterar aktuella ICA-erbjudanden":"ICA-data ej verifierad just nu"}</div></div></div>${state.week.map((p,i)=>`<div class="card week-card">${image(p.recipe,"thumb")}<div class="week-main"><div class="day">${p.day}</div><div class="source-badge">${esc(p.recipe.source||"Matappen")}</div><div class="meal">${esc(p.recipe.name)}</div><div class="row">${meta(p.recipe)}</div>${offerBadge(p.recipe)}<div class="week-actions"><button class="secondary-btn" data-recipeid="${esc(p.recipe.id)}">Recept</button><button class="secondary-btn" data-swap="${i}">↻ Byt</button></div></div></div>`).join("")}</section>`;
}
function parseIngredient(line){
 let s=String(line||"").trim(),name=s,qty="",unit="";
 let m=s.match(/^(.+?):\s*([\d.,½¼¾⅓⅔]+)\s*([a-zA-ZåäöÅÄÖ]+)?/);
 if(m){name=m[1].trim();qty=m[2];unit=m[3]||"";return {name,qty,unit,raw:s}}
 m=s.match(/^([\d.,½¼¾⅓⅔]+)\s*([a-zA-ZåäöÅÄÖ]+)?\s+(.+)$/);
 if(m){qty=m[1];unit=m[2]||"";name=m[3].replace(/^av\s+/i,"").trim();return {name,qty,unit,raw:s}}
 return {name:s,qty:"",unit:"",raw:s};
}
function num(s){if(!s)return null;s=String(s).replace(",",".");const f={"½":.5,"¼":.25,"¾":.75,"⅓":1/3,"⅔":2/3};if(f[s])return f[s];let n=parseFloat(s);return Number.isFinite(n)?n:null}
function unitKey(u){u=canon(u);if(["gram","g"].includes(u))return"g";if(["kilogram","kg"].includes(u))return"kg";if(["deciliter","dl"].includes(u))return"dl";if(["milliliter","ml"].includes(u))return"ml";if(["stycken","styck","st"].includes(u))return"st";return u}
function shopping(){
 let map=new Map();
 state.week.forEach(p=>(p.recipe.ingredients||[]).forEach(line=>{
   const x=parseIngredient(line),key=canon(x.name),u=unitKey(x.unit),n=num(x.qty),k=key+"|"+u;
   if(n!==null){
     if(!map.has(k))map.set(k,{name:x.name,unit:u,qty:0,offers:[]});
     map.get(k).qty+=n;
   }else{
     let rk=key+"|";if(!map.has(rk))map.set(rk,{name:x.name,unit:"",qty:null,raw:x.raw,offers:[]});
   }
 }));
 state.quick.forEach(x=>{let k=canon(x)+"|";if(!map.has(k))map.set(k,{name:x,unit:"",qty:null,raw:x,offers:[]})});
 for(const item of map.values()){
   if(state.offerStatus==="live")item.offers=state.offers.filter(o=>words(o.name).some(w=>canon(item.name).includes(w)||canon(o.name).includes(words(item.name)[0]||"___"))).slice(0,1);
 }
 return [...map.values()].sort((a,b)=>a.name.localeCompare(b.name,"sv"));
}
function fmtQty(x){if(x.qty===null)return "";let q=Math.round(x.qty*100)/100;if(x.unit==="g"&&q>=1000)return `${Math.round(q/100)/10} kg`;if(x.unit==="ml"&&q>=1000)return `${Math.round(q/100)/10} l`;return `${String(q).replace(".",",")} ${x.unit}`.trim()}
function shopView(){
 const items=shopping();
 return `<section class="section" style="margin-top:4px"><div class="section-head"><div><h2>Inköpslista</h2><div class="muted">Mängder från hela veckans recept slås ihop</div></div><button class="section-link" id="addCustom">＋ Lägg till</button></div>${items.map((x,i)=>`<div class="check-row ${state.checked.has(x.name)?"done":""}"><input type="checkbox" data-check="${esc(x.name)}" ${state.checked.has(x.name)?"checked":""}><label><b>${esc(x.name)}</b>${fmtQty(x)?`<span class="quantity">${esc(fmtQty(x))}</span>`:""}${x.offers.length?`<small class="deal-line">🔥 ICA: ${esc(x.offers[0].name)}${x.offers[0].price?` · ${esc(x.offers[0].price)}`:""}</small>`:""}</label></div>`).join("")}<div style="height:14px"></div><button class="secondary-btn" id="clearBought">Ta bort köpta</button></section>`;
}
function recipeView(){
 const external=state.recipes.filter(r=>r.external).length;
 return `<section class="section" style="margin-top:4px"><div class="section-head"><div><h2>Recept</h2><div class="muted">${state.recipes.length} recept · ${external} externa</div></div></div><input class="search" id="search" placeholder="Sök kyckling, pasta, gryta…"><div class="filter-row">${["Alla","👍 Gillade","🔥 ICA-match","≤30 min","ICA","Arla","Köket"].map((x,i)=>`<button class="filter ${i===0?"active":""}" data-filter="${x}">${x}</button>`).join("")}</div><div id="recipeList">${recipeCards(state.recipes.slice(0,180))}</div></section>`;
}
function recipeCards(arr){return arr.map(r=>`<div class="card recipe-card" data-id="${esc(r.id)}">${image(r,"card-image")}<div class="source-badge">${esc(r.source||"Matappen")}${state.liked.has(r.name)?" · 👍 Gillad":""}</div><div class="meal">${esc(r.name)}</div><div class="row">${meta(r)}</div>${offerBadge(r)}</div>`).join("")}
function wire(){
 document.querySelectorAll("[data-recipeid]").forEach(b=>b.onclick=()=>showRecipe(b.dataset.recipeid));
 document.querySelectorAll(".recipe-card").forEach(c=>c.onclick=()=>showRecipe(c.dataset.id));
 document.querySelectorAll("[data-swap]").forEach(b=>b.onclick=()=>swapMeal(Number(b.dataset.swap)));
 document.querySelectorAll("[data-add]").forEach(b=>b.onclick=()=>addQuick(b.dataset.add));
 document.querySelectorAll("[data-check]").forEach(c=>c.onchange=()=>{c.checked?state.checked.add(c.dataset.check):state.checked.delete(c.dataset.check);localStorage.setItem("checked",JSON.stringify([...state.checked]))});
 if($("#clearBought"))$("#clearBought").onclick=()=>{state.quick=state.quick.filter(x=>!state.checked.has(x));localStorage.setItem("quick",JSON.stringify(state.quick));state.checked.clear();localStorage.removeItem("checked");render()};
 if($("#addCustom"))$("#addCustom").onclick=customAdd;if($("#search"))$("#search").oninput=filterRecipes;
 document.querySelectorAll("[data-filter]").forEach(b=>b.onclick=()=>{document.querySelectorAll("[data-filter]").forEach(x=>x.classList.remove("active"));b.classList.add("active");state.filter=b.dataset.filter;filterRecipes()});
}
function addQuick(v){if(!state.quick.includes(v))state.quick.push(v);state.quickStats[v]=(state.quickStats[v]||0)+1;localStorage.setItem("quick",JSON.stringify(state.quick));localStorage.setItem("quickStats",JSON.stringify(state.quickStats));toast(`${v} tillagd`);render()}
function swapMeal(i){
 const cur=state.week[i].recipe;let pool=state.recipes.filter(r=>r.name!==cur.name&&!state.disliked.has(r.name)&&!state.week.some((p,j)=>j!==i&&p.recipe.name===r.name));
 pool.sort((a,b)=>score(b,i)-score(a,i));if(pool.length)state.week[i].recipe=pool[0];render();toast("Bytte middag");
}
function showRecipe(id){
 const r=state.recipes.find(x=>x.id===id)||state.week.map(x=>x.recipe).find(x=>x.id===id);if(!r)return;
 const liked=state.liked.has(r.name),disliked=state.disliked.has(r.name);
 let body=`${image(r,"sheet-image")}<div class="source-badge">${esc(r.source||"Matappen")}</div><h3>${esc(r.name)}</h3><div class="row">${meta(r)}</div>${offerBadge(r)}
 <div class="taste-actions"><button class="${liked?"taste-on":""}" id="likeRecipe">👍 ${liked?"Gillad":"Den här gillar vi"}</button><button class="${disliked?"taste-bad":""}" id="dislikeRecipe">👎 ${disliked?"Undviks":"Inte för oss"}</button></div>`;
 if((r.ingredients||[]).length)body+=`<h4>Ingredienser</h4>${r.ingredients.map(x=>`<div class="ingredient">${esc(x)}</div>`).join("")}`;
 if(r.external&&r.url)body+=`<p class="muted">Tillagningen öppnas hos originalkällan.</p><a href="${esc(r.url)}" target="_blank" rel="noopener" class="wide-btn link-btn">Öppna hos ${esc(r.source)} ↗</a>`;
 else if(r.steps)body+=`<h4>Gör så här</h4>${r.steps.map((s,i)=>`<div class="step"><b>${i+1}.</b> ${esc(s)}</div>`).join("")}`;
 showSheet(body);
 setTimeout(()=>{
   $("#likeRecipe").onclick=()=>{state.liked.add(r.name);state.disliked.delete(r.name);saveTaste();buildWeek();closeSheet();render();toast("👍 Sparat – påverkar framtida veckor")};
   $("#dislikeRecipe").onclick=()=>{state.disliked.add(r.name);state.liked.delete(r.name);saveTaste();buildWeek();closeSheet();render();toast("👎 Sparat – receptet undviks")};
 },10);
}
function saveTaste(){localStorage.setItem("liked",JSON.stringify([...state.liked]));localStorage.setItem("disliked",JSON.stringify([...state.disliked]))}
function filterRecipes(){
 const q=$("#search").value.toLowerCase().trim(),f=state.filter;let arr=state.recipes.filter(r=>(r.name+" "+(r.ingredients||[]).join(" ")+" "+(r.tags||[]).join(" ")).toLowerCase().includes(q));
 if(f==="≤30 min")arr=arr.filter(r=>mins(r)&&mins(r)<=30);if(["ICA","Arla","Köket"].includes(f))arr=arr.filter(r=>r.source===f);if(f==="👍 Gillade")arr=arr.filter(r=>state.liked.has(r.name));if(f==="🔥 ICA-match")arr=arr.filter(r=>offerMatches(r).length);
 $("#recipeList").innerHTML=recipeCards(arr.slice(0,220));document.querySelectorAll(".recipe-card").forEach(c=>c.onclick=()=>showRecipe(c.dataset.id));
}
function showInfo(){showSheet(`<h3>Matappen v17</h3><p><b>Veckoplaneringen väger nu ICA-erbjudanden tyngst.</b> Därefter familjens 👍/👎, vardagstid, matlådor, frys och variation.</p><p class="muted">ICA-status: ${esc(state.offerStatus)} · ${state.offers.length} erbjudanden i filen. Bara status “live” får påverka planeringen.</p><button class="secondary-btn" id="clearTaste">Återställ 👍/👎</button>`);setTimeout(()=>{$("#clearTaste").onclick=()=>{state.liked.clear();state.disliked.clear();saveTaste();buildWeek();closeSheet();render();toast("Smakprofil återställd")}},10)}
function customAdd(){showSheet(`<h3>Lägg till vara</h3><input class="search" id="customInput" placeholder="T.ex. kaffe"><button class="wide-btn" id="saveCustom">Lägg till</button>`);setTimeout(()=>{$("#saveCustom").onclick=()=>{const v=$("#customInput").value.trim();if(v)addQuick(v);closeSheet();render()}},10)}
function showSheet(html){$("#sheet").innerHTML=html;$("#sheetBackdrop").classList.remove("hidden");$("#sheet").classList.remove("hidden");$("#sheetBackdrop").onclick=closeSheet}
function closeSheet(){$("#sheetBackdrop").classList.add("hidden");$("#sheet").classList.add("hidden")}
function toast(msg){let t=document.createElement("div");t.textContent=msg;t.className="toast";document.body.appendChild(t);setTimeout(()=>t.remove(),1900)}
init();
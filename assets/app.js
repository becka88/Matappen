let state={recipes:[],view:"today",week:[],disliked:new Set(JSON.parse(localStorage.getItem("disliked")||"[]")),checked:new Set(),quick:JSON.parse(localStorage.getItem("quick")||"[]"),filter:"Alla"};
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
const mins=r=>r.minutes??null;
function score(r,i){
 let s=0, m=mins(r);
 if(i<4 && m && m<=35)s+=12;
 if(r.lunch>=4)s+=6;
 if(r.freeze>=4)s+=3;
 if((r.tags||[]).includes("barnvänlig"))s+=4;
 if(i===4 && ((r.tags||[]).includes("fredag")||/taco|burrito|quesadilla/i.test(r.name)))s+=15;
 if(state.disliked.has(r.name))s-=999;
 return s+Math.random()*3;
}
function buildWeek(){
 const used=new Set(); state.week=[];
 for(let i=0;i<7;i++){
   let pool=state.recipes.filter(r=>!used.has(r.name)&&!state.disliked.has(r.name));
   if(!pool.length) pool=state.recipes;
   pool=[...pool].sort((a,b)=>score(b,i)-score(a,i));
   let r=pool[0]; used.add(r.name); state.week.push({day:["Måndag","Tisdag","Onsdag","Torsdag","Fredag","Lördag","Söndag"][i],recipe:r});
 }
}
async function init(){
 try{
   const r=await fetch("./recipes.json?"+Date.now());
   state.recipes=await r.json();
   buildWeek(); render(); bindNav();
 }catch(e){$("#view").innerHTML='<div class="card">Kunde inte läsa receptkatalogen just nu.</div>'}
}
function bindNav(){
 document.querySelectorAll(".nav-btn").forEach(b=>b.onclick=()=>{
   state.view=b.dataset.view;
   document.querySelectorAll(".nav-btn").forEach(x=>x.classList.toggle("active",x===b));
   render(); window.scrollTo({top:0,behavior:"smooth"});
 });
 $("#profileBtn").onclick=()=>showInfo();
}
function meta(r){
 let a=[]; if(mins(r))a.push(`⏱ ${mins(r)} min`);
 if(r.external)a.push(`↗ ${r.source}`);
 else {if(r.lunch)a.push(`🥡 ${r.lunch}/5`);if(r.freeze)a.push(`❄️ ${r.freeze}/5`)}
 return a.map(x=>`<span class="soft-chip">${esc(x)}</span>`).join("");
}
function render(){
 if(state.view==="today")$("#view").innerHTML=todayView();
 if(state.view==="week")$("#view").innerHTML=weekView();
 if(state.view==="shop")$("#view").innerHTML=shopView();
 if(state.view==="recipes")$("#view").innerHTML=recipeView();
 wire();
}
function todayView(){
 const d=new Date().getDay(),idx=d===0?6:d-1,p=state.week[idx],t=state.week[(idx+1)%7];
 return `<section class="hero-card"><div class="hero-label">${p.day} · dagens middag</div><div class="hero-title">${esc(p.recipe.name)}</div><div class="meta">${meta(p.recipe)}</div><div class="hero-actions"><button class="light" data-recipeid="${esc(p.recipe.id)}">Visa recept</button><button class="ghost" data-dislike="${idx}">👎 Inte sugen</button></div></section>
 <section class="section"><div class="section-head"><h2>Lägg till snabbt</h2></div><div class="quick-grid">${["Mjölk","Bröd","Ägg","Diskmedel"].map(x=>`<button class="quick" data-add="${x}">＋ ${x}<small>till inköpslistan</small></button>`).join("")}</div></section>
 <section class="section"><div class="section-head"><h2>I morgon</h2></div><div class="card"><div class="day">${t.day}</div><div class="meal">${esc(t.recipe.name)}</div><div class="row">${meta(t.recipe)}</div></div></section>`;
}
function weekView(){
 return `<section class="section" style="margin-top:4px"><div class="section-head"><h2>Veckans middagar</h2></div>${state.week.map((p,i)=>`<div class="card"><div class="day">${p.day}</div><div class="source-badge">${esc(p.recipe.source||"Matappen")}</div><div class="meal">${esc(p.recipe.name)}</div><div class="row">${meta(p.recipe)}</div><div style="margin-top:13px;display:grid;grid-template-columns:1fr 1fr;gap:8px"><button class="secondary-btn" data-recipeid="${esc(p.recipe.id)}">Recept</button><button class="secondary-btn" data-dislike="${i}">👎 Byt</button></div></div>`).join("")}</section>`;
}
function ingredients(r){return r.ingredients||[]}
function allShopping(){let s=new Set(state.quick);state.week.forEach(p=>ingredients(p.recipe).forEach(x=>s.add(String(x).split(":")[0].trim())));return [...s].filter(Boolean).sort((a,b)=>a.localeCompare(b,"sv"))}
function shopView(){
 const items=allShopping();
 return `<section class="section" style="margin-top:4px"><div class="section-head"><h2>Inköpslista</h2><button class="section-link" id="addCustom">＋ Lägg till</button></div>${items.map(x=>`<div class="check-row"><input type="checkbox" data-check="${esc(x)}" ${state.checked.has(x)?"checked":""}><label>${esc(x)}</label></div>`).join("")}<div style="height:14px"></div><button class="secondary-btn" id="clearBought">Ta bort köpta</button></section>`;
}
function recipeView(){
 const external=state.recipes.filter(r=>r.external).length;
 return `<section class="section" style="margin-top:4px"><div class="section-head"><div><h2>Recept</h2><div class="muted">${state.recipes.length} recept · ${external} från externa källor</div></div></div>
 <div class="catalog-note">Katalogen uppdateras automatiskt av GitHub. Nya recept från ICA, Arla och Köket dyker upp här utan att du behöver göra något.</div>
 <input class="search" id="search" placeholder="Sök t.ex. kyckling, pasta, gryta…">
 <div class="filter-row">${["Alla","≤30 min","ICA","Arla","Köket"].map((x,i)=>`<button class="filter ${i===0?"active":""}" data-filter="${x}">${x}</button>`).join("")}</div>
 <div id="recipeList">${recipeCards(state.recipes.slice(0,160))}</div></section>`;
}
function recipeCards(arr){return arr.map(r=>`<div class="card recipe-card" data-id="${esc(r.id)}"><div class="source-badge">${esc(r.source||"Matappen")}</div><div class="meal">${esc(r.name)}</div><div class="row">${meta(r)}</div></div>`).join("")}
function wire(){
 document.querySelectorAll("[data-recipeid]").forEach(b=>b.onclick=()=>showRecipe(b.dataset.recipeid));
 document.querySelectorAll(".recipe-card").forEach(c=>c.onclick=()=>showRecipe(c.dataset.id));
 document.querySelectorAll("[data-dislike]").forEach(b=>b.onclick=()=>replaceMeal(Number(b.dataset.dislike)));
 document.querySelectorAll("[data-add]").forEach(b=>b.onclick=()=>{if(!state.quick.includes(b.dataset.add))state.quick.push(b.dataset.add);localStorage.setItem("quick",JSON.stringify(state.quick));toast(`${b.dataset.add} tillagd`)});
 document.querySelectorAll("[data-check]").forEach(c=>c.onchange=()=>c.checked?state.checked.add(c.dataset.check):state.checked.delete(c.dataset.check));
 if($("#clearBought"))$("#clearBought").onclick=()=>{state.quick=state.quick.filter(x=>!state.checked.has(x));localStorage.setItem("quick",JSON.stringify(state.quick));state.checked.clear();render()};
 if($("#addCustom"))$("#addCustom").onclick=customAdd;
 if($("#search"))$("#search").oninput=filterRecipes;
 document.querySelectorAll("[data-filter]").forEach(b=>b.onclick=()=>{document.querySelectorAll("[data-filter]").forEach(x=>x.classList.remove("active"));b.classList.add("active");state.filter=b.dataset.filter;filterRecipes()});
}
function replaceMeal(i){
 const cur=state.week[i].recipe; state.disliked.add(cur.name); localStorage.setItem("disliked",JSON.stringify([...state.disliked]));
 let pool=state.recipes.filter(r=>!state.disliked.has(r.name)&&!state.week.some((p,j)=>j!==i&&p.recipe.name===r.name));
 pool.sort((a,b)=>score(b,i)-score(a,i)); if(pool.length)state.week[i].recipe=pool[0]; render();toast("Bytte middag");
}
function showRecipe(id){
 const r=state.recipes.find(x=>x.id===id)||state.week.map(x=>x.recipe).find(x=>x.id===id);if(!r)return;
 let body=`<div class="source-badge">${esc(r.source||"Matappen")}</div><h3>${esc(r.name)}</h3><div class="row">${meta(r)}</div>`;
 if(r.image)body+=`<img src="${esc(r.image)}" style="width:100%;border-radius:18px;margin-top:14px" alt="">`;
 if(ingredients(r).length)body+=`<h4>Ingredienser</h4>${ingredients(r).map(x=>`<div class="ingredient">${esc(x)}</div>`).join("")}`;
 if(r.external&&r.url)body+=`<p class="muted">Tillagningen läser du hos originalkällan.</p><a href="${esc(r.url)}" target="_blank" rel="noopener" class="wide-btn" style="display:block;text-decoration:none;text-align:center">Öppna hos ${esc(r.source)} ↗</a>`;
 else if(r.steps)body+=`<h4>Gör så här</h4>${r.steps.map((s,i)=>`<div class="step"><b>${i+1}.</b> ${esc(s)}</div>`).join("")}`;
 showSheet(body);
}
function filterRecipes(){
 const q=$("#search").value.toLowerCase().trim(),f=state.filter;
 let arr=state.recipes.filter(r=>(r.name+" "+ingredients(r).join(" ")+" "+(r.tags||[]).join(" ")).toLowerCase().includes(q));
 if(f==="≤30 min")arr=arr.filter(r=>mins(r)&&mins(r)<=30);
 if(["ICA","Arla","Köket"].includes(f))arr=arr.filter(r=>r.source===f);
 $("#recipeList").innerHTML=recipeCards(arr.slice(0,220));document.querySelectorAll(".recipe-card").forEach(c=>c.onclick=()=>showRecipe(c.dataset.id));
}
function showInfo(){showSheet(`<h3>Matappen</h3><p>Mobilversionen körs direkt från GitHub Pages. Receptkatalogen uppdateras automatiskt i GitHub.</p><button class="wide-btn" id="clearDisliked">Återställ nedröstade recept</button>`);setTimeout(()=>{$("#clearDisliked").onclick=()=>{state.disliked.clear();localStorage.removeItem("disliked");buildWeek();closeSheet();render();toast("Återställt")}},10)}
function customAdd(){showSheet(`<h3>Lägg till vara</h3><input class="search" id="customInput" placeholder="T.ex. kaffe"><button class="wide-btn" id="saveCustom">Lägg till</button>`);setTimeout(()=>{$("#saveCustom").onclick=()=>{const v=$("#customInput").value.trim();if(v&&!state.quick.includes(v)){state.quick.push(v);localStorage.setItem("quick",JSON.stringify(state.quick))}closeSheet();render()}},10)}
function showSheet(html){$("#sheet").innerHTML=html;$("#sheetBackdrop").classList.remove("hidden");$("#sheet").classList.remove("hidden");$("#sheetBackdrop").onclick=closeSheet}
function closeSheet(){$("#sheetBackdrop").classList.add("hidden");$("#sheet").classList.add("hidden")}
function toast(msg){let t=document.createElement("div");t.textContent=msg;t.style.cssText="position:fixed;left:50%;bottom:92px;transform:translateX(-50%);background:#243A2E;color:white;padding:11px 14px;border-radius:999px;font-weight:800;z-index:99;max-width:88%;text-align:center";document.body.appendChild(t);setTimeout(()=>t.remove(),1600)}
init();
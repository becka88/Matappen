let state={
 recipes:[],offers:[],offerStatus:"waiting",view:"today",week:[],
 liked:new Set(JSON.parse(localStorage.getItem("likedV24")||"[]")),
 disliked:new Set(JSON.parse(localStorage.getItem("dislikedV24")||"[]")),
 checked:new Set(JSON.parse(localStorage.getItem("checked")||"[]")),
 quick:JSON.parse(localStorage.getItem("quick")||"[]"),quickStats:JSON.parse(localStorage.getItem("quickStats")||"{}"),
 filter:"Alla",customRecipes:JSON.parse(localStorage.getItem("customRecipes")||"[]"),
 hiddenShop:new Set(JSON.parse(localStorage.getItem("hiddenShopV24")||"[]")),
 settings:JSON.parse(localStorage.getItem("familySettingsV24")||'{"handover":"arrival","handoverDay":4,"weeklyBudget":1600,"monthlyBudget":12000}'),
 expenses:JSON.parse(localStorage.getItem("expensesV24")||"[]")
};
const $=s=>document.querySelector(s), esc=s=>String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
const days=["Måndag","Tisdag","Onsdag","Torsdag","Fredag","Lördag","Söndag"];
const canon=s=>String(s||"").toLowerCase().replace(/[,:()]/g," ").replace(/filéer/g,"filé").replace(/kycklingbröst/g,"kycklingfilé").replace(/färsen/g,"färs").replace(/\s+/g," ").trim();
const recipeKey=r=>String(r.id||((r.source||"")+":"+(r.name||"")));
const mins=r=>r.minutes??null;
function isoWeek(d=new Date()){let x=new Date(Date.UTC(d.getFullYear(),d.getMonth(),d.getDate()));x.setUTCDate(x.getUTCDate()+4-(x.getUTCDay()||7));let y=new Date(Date.UTC(x.getUTCFullYear(),0,1));return Math.ceil((((x-y)/86400000)+1)/7)}
function weekKey(){let d=new Date();return `${d.getFullYear()}-W${isoWeek(d)}`}
function save(){localStorage.setItem("familySettingsV24",JSON.stringify(state.settings));localStorage.setItem("expensesV24",JSON.stringify(state.expenses));localStorage.setItem("hiddenShopV24",JSON.stringify([...state.hiddenShop]));}
function isKidsDay(i){const childWeek=isoWeek()%2===0;const before=i<3; if(state.settings.handover==="arrival") return childWeek ? !before : before; return childWeek ? before : !before;}
function targetPortions(i){return isKidsDay(i)?6:4}
const offerRules=[
 ["filled_pasta",/\b(fylld pasta|tortellini|ravioli)\b/,/\b(fylld pasta|tortellini|ravioli)\b/,4],
 ["dry_pasta",/\b(spaghetti|penne|makaron|torr pasta)\b/,/\b(spaghetti|penne|makaron|torr pasta)\b/,3],
 ["chicken",/\bkycklingfil[eé]\b/,/\b(kycklingfil[eé]|kycklingbröst)\b/,5],["mince",/\b(nötfärs|blandfärs|köttfärs|färs)\b/,/\b(nötfärs|blandfärs|köttfärs|färs)\b/,5],
 ["salmon",/\blax\b/,/\blax\b/,5],["cod",/\btorsk\b/,/\btorsk\b/,5],["sausage",/\b(falukorv|middagskorv)\b/,/\b(falukorv|middagskorv)\b/,5],
 ["cheese",/\b(herrgård|präst|grevé|hushållsost|hårdost|riven ost)\b/,/\b(hårdost|riven ost|ost)\b/,2],["potato",/\bpotatis\b/,/\bpotatis\b/,2],["carrot",/\bmorötter?\b/,/\bmorötter?\b/,2],["corn",/\bmajs\b/,/\bmajs\b/,2],["creme",/\bcr[eè]me fraiche\b/,/\bcr[eè]me fraiche\b/,2]
];
function matchOfferToRecipe(o,r){const ot=canon((o.name||"")+" "+(o.details||"")),rt=canon((r.name||"")+" "+(r.ingredients||[]).join(" "));for(const [,ore,rre,w] of offerRules)if(ore.test(ot))return rre.test(rt)?w:0;return 0}
function offerMatches(r){if(state.offerStatus!=="live")return[];return state.offers.map(o=>({offer:o,weight:matchOfferToRecipe(o,r)})).filter(x=>x.weight>0).sort((a,b)=>b.weight-a.weight).slice(0,4)}
function mainGroup(r){const t=canon((r.name||"")+" "+(r.ingredients||[]).join(" "));for(const [g,re] of [["falukorv",/\bfalukorv\b/],["korv",/\bkorv\b/],["kyckling",/\bkyckling\b/],["lax",/\blax\b/],["fisk",/\b(?:torsk|sej|fisk)\b/],["färs",/\b(?:köttfärs|nötfärs|blandfärs|färs)\b/],["fläsk",/\b(?:fläsk|kotlett|fläskfilé)\b/],["vegetariskt",/\b(?:linser|bönor|tofu|halloumi|vegetar)\b/]])if(re.test(t))return g;return "annat"}
function baseScore(r,i,counts){let s=0,key=recipeKey(r),m=mins(r),kids=isKidsDay(i),g=mainGroup(r),matches=offerMatches(r);if(state.liked.has(key))s+=28;if(state.disliked.has(key))return-9999;if(matches.length)s+=Math.min(22,8+matches.reduce((n,x)=>n+x.weight,0)*2);if(counts[g])s-=g==="annat"?8:55*counts[g];if(kids){if((r.tags||[]).includes("barnvänlig")||/taco|pasta|köttbull|pannkak|mild/i.test(r.name))s+=12;if(/stark|chili/i.test(r.name))s-=12}else{if(/curry|chili|gryta|asiat/i.test(r.name))s+=5}if(i<4&&m&&m<=35)s+=8;if(i===4&&/taco|pizza|burg|quesadilla/i.test(r.name))s+=10;return s}
function buildWeek(){let used=new Set(),counts={},week=[];for(let i=0;i<7;i++){let pool=state.recipes.filter(r=>!used.has(recipeKey(r))&&!state.disliked.has(recipeKey(r)));pool.sort((a,b)=>baseScore(b,i,counts)-baseScore(a,i,counts));let r=pool[0];if(!r)continue;used.add(recipeKey(r));let g=mainGroup(r);counts[g]=(counts[g]||0)+1;week.push({day:days[i],recipe:r,kids:isKidsDay(i),portions:targetPortions(i)});}state.week=week;resetHiddenForWeek()}
function resetHiddenForWeek(){const k="hiddenShopWeekV24";if(localStorage.getItem(k)!==weekKey()){state.hiddenShop.clear();localStorage.setItem(k,weekKey());localStorage.setItem("hiddenShopV24","[]")}}
async function init(){try{const[rr,oo]=await Promise.all([fetch("./recipes.json?"+Date.now()).then(r=>r.json()),fetch("./offers.json?"+Date.now()).then(r=>r.ok?r.json():({status:"unavailable",offers:[]}))]);state.recipes=[...state.customRecipes,...rr];state.offerStatus=oo.status||"unavailable";state.offers=oo.offers||[];buildWeek();render();bindNav()}catch(e){$("#view").innerHTML='<div class="card">Kunde inte läsa Matappens data just nu.</div>'}}
function bindNav(){document.querySelectorAll(".nav-btn").forEach(b=>b.onclick=()=>{state.view=b.dataset.view;document.querySelectorAll(".nav-btn").forEach(x=>x.classList.toggle("active",x===b));render();scrollTo(0,0)});$("#profileBtn").onclick=showInfo}
function image(r,cls="recipe-image"){return r.image?`<img class="${cls}" src="${esc(r.image)}" alt="" loading="lazy" referrerpolicy="no-referrer">`:""}
function meta(r){let a=[];if(mins(r))a.push(`⏱ ${mins(r)} min`);if(r.external)a.push(`↗ ${r.source}`);return a.map(x=>`<span class="soft-chip">${esc(x)}</span>`).join("")}
function offerBadge(r){let m=offerMatches(r);if(!m.length)return"";return `<div class="offer">🔥 Passar veckans erbjudande: ${m.map(x=>`<b>${esc(x.offer.name)}</b>`).join(" + ")}</div>`}
function familyChip(p){return `<span class="family-chip ${p.kids?'kids':'adult'}">${p.kids?'👨‍👩‍👧‍👦 Barnen hemma':'🌶️ Vuxenkväll'} · ${p.portions} port</span>`}
function render(){if(state.view==="today")$("#view").innerHTML=todayView();if(state.view==="week")$("#view").innerHTML=weekView();if(state.view==="shop")$("#view").innerHTML=shopView();if(state.view==="recipes")$("#view").innerHTML=recipeView();wire()}
function todayView(){
 let d=new Date().getDay(),i=d===0?6:d-1,p=state.week[i]||state.week[0],t=state.week[(i+1)%7];
 let remaining=shopping().filter(x=>!state.checked.has(x.key)).length;
 return `<section class="hero-card">${image(p.recipe,"hero-image")}
 <div class="hero-label">${p.day} · dagens middag</div>
 <div class="hero-title">${esc(p.recipe.name)}</div>
 <div class="meta">${familyChip(p)}${meta(p.recipe)}</div>${offerBadge(p.recipe)}
 <div class="hero-actions"><button class="light" data-recipeid="${esc(recipeKey(p.recipe))}">Visa recept</button><button class="ghost" data-swap="${i}">↻ Byt rätt</button></div></section>
 <div class="home-glance">
   <button class="glance-card" data-goto="shop"><span class="glance-icon">🛒</span><span><b>${remaining} saker kvar</b><small>Öppna inköpslistan</small></span><span class="chev">›</span></button>
 </div>
 <div class="budget-card">${budgetSummary()}</div>
 <div class="status-line ${state.offerStatus==='live'?'ok':'warn'}">${state.offerStatus==='live'?`${state.offers.length} verifierade ICA-erbjudanden används som bonus i planeringen`:'ICA-erbjudanden kunde inte verifieras – veckan byggs utan dem'}</div>
 <section class="section"><div class="section-head"><div><h2>I morgon</h2><div class="muted">Nästa middag i planen</div></div></div>
 <div class="card mini-meal">${image(t.recipe,"thumb")}<div><div class="day">${t.day}</div><div class="meal">${esc(t.recipe.name)}</div>${familyChip(t)}${offerBadge(t.recipe)}</div></div></section>`;
}
function weekView(){
 return `<section class="page-head"><span class="kicker">Veckoplan</span><h1>Veckans middagar</h1><p>Variation först. Erbjudanden hjälper till, men styr inte hela veckan.</p></section>
 <section class="week-list">${state.week.map((p,i)=>`<article class="card week-card">${image(p.recipe,"thumb")}<div class="week-main"><div class="day">${p.day}</div><div class="meal">${esc(p.recipe.name)}</div>${familyChip(p)}<div class="row">${meta(p.recipe)}</div>${offerBadge(p.recipe)}<div class="week-actions"><button class="secondary-btn" data-recipeid="${esc(recipeKey(p.recipe))}">Visa recept</button><button class="tertiary-btn" data-swap="${i}">↻ Byt</button></div></div></article>`).join("")}</section>`;
}
function parseIngredient(line){let s=String(line||"").trim(),m=s.match(/^(.+?):\s*([\d.,½¼¾⅓⅔]+)\s*([a-zA-ZåäöÅÄÖ]+)?/);if(m)return{name:m[1].trim(),qty:m[2],unit:m[3]||""};m=s.match(/^([\d.,½¼¾⅓⅔]+)\s*([a-zA-ZåäöÅÄÖ]+)?\s+(.+)$/);if(m)return{name:m[3].trim(),qty:m[1],unit:m[2]||""};return{name:s,qty:"",unit:""}}
function num(s){if(!s)return null;const f={"½":.5,"¼":.25,"¾":.75,"⅓":1/3,"⅔":2/3};if(f[s])return f[s];let n=parseFloat(String(s).replace(",","."));return Number.isFinite(n)?n:null}
function unitKey(u){u=canon(u);if(["gram","g"].includes(u))return"g";if(["kilogram","kg"].includes(u))return"kg";if(["deciliter","dl"].includes(u))return"dl";if(["milliliter","ml"].includes(u))return"ml";if(["liter","l"].includes(u))return"l";if(["stycken","styck","st"].includes(u))return"st";if(["burkar","burk"].includes(u))return"burk";if(["förpackningar","förpackning","förp","paket","pkt"].includes(u))return"förp";return u}
function shopName(n){n=canon(n).replace(/\([^)]*\)/g," ").replace(/\b(?:ca|cirka|avrunnen|avrunnet|konserverad|konserverade)\b/g," ").replace(/\b(?:på|i)\s+burk\b/g," ").replace(/\s+/g," ").trim();for(const[re,to]of[[/^(?:majskorn|sötmajs|majs(?:korn)?)$/,"majs"],[/^(?:gul lök|gula lökar)$/,"gul lök"],[/^(?:vitlöksklyfta|vitlöksklyftor|vitlök)$/,"vitlök"],[/^(?:krossad tomat|krossade tomater)$/,"krossade tomater"]])if(re.test(n))return to;return n}
function expandIngredient(line){let raw=String(line||"").trim(),c=canon(raw);if(!raw||/^(?:till servering|servering|garnering|sås|dressing|marinad)\s*:?\s*$/i.test(raw))return[];if(/\bkebabsås\b/.test(c)&&/\b(?:hemmagjord|hemgjord|se (?:länk|recept))\b/.test(c))return["2 dl turkisk yoghurt","1 dl majonnäs","1 vitlöksklyfta","1 tsk paprikapulver"];if(/\b(?:se länk|se recept|enligt recept|recept finns)\b/.test(c))return[];return[raw]}
function shopping(){let map=new Map(),never=new Set(["vatten","kranvatten"]);const add=(x,factor=1)=>{let key=shopName(x.name),u=unitKey(x.unit),n=num(x.qty);if(!key||never.has(key))return;let k=key+"|"+u,item=map.get(k);if(!item){item={key,name:key,unit:u,qty:n===null?null:0,offers:[]};map.set(k,item)}if(n!==null){if(item.qty===null)item.qty=0;item.qty+=n*factor}};state.week.forEach(p=>{let factor=p.portions/Number(p.recipe.portions||4);(p.recipe.ingredients||[]).forEach(line=>expandIngredient(line).forEach(x=>add(parseIngredient(x),factor)))});state.quick.forEach(x=>add({name:x,qty:"",unit:""}));for(const item of map.values())if(state.offerStatus==="live")item.offers=state.offers.filter(o=>matchOfferToRecipe(o,{name:item.name,ingredients:[item.name]})>0).slice(0,1);return[...map.values()].filter(x=>!state.hiddenShop.has(x.key)).sort((a,b)=>a.name.localeCompare(b.name,"sv"))}
function fmtQty(x){if(x.qty===null)return"";let q=Math.round(x.qty*100)/100;if(x.unit==="g"&&q>=1000)return`${Math.round(q/100)/10} kg`;if(x.unit==="ml"&&q>=1000)return`${Math.round(q/100)/10} l`;return`${String(q).replace(".",",")} ${x.unit}`.trim()}
function offerCost(o){let p=canon(o.price),m=p.match(/(\d+) för (\d+(?:[.,]\d+)?)/);if(m)return Number(m[2].replace(",","."))/Number(m[1]);m=p.match(/(\d+(?:[.,]\d+)?) kr\/st/);return m?Number(m[1].replace(",",".")):null}
function estimateShop(){let known=0,count=0,total=shopping().length;shopping().forEach(x=>{if(x.offers[0]){let p=offerCost(x.offers[0]);if(p){known+=p;count++}}});return{known,count,total}}
function monthSpent(){let d=new Date(),ym=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`;return state.expenses.filter(x=>x.date.startsWith(ym)).reduce((n,x)=>n+Number(x.amount||0),0)}
function budgetSummary(){
 let spent=monthSpent(),left=Math.max(0,state.settings.monthlyBudget-spent),pct=Math.min(100,Math.round(spent/state.settings.monthlyBudget*100)||0),est=estimateShop();
 return `<div class="budget-head"><div><span class="kicker">Månadsbudget</span><strong>${Math.round(spent).toLocaleString('sv-SE')} kr</strong></div><span class="budget-left">${Math.round(left).toLocaleString('sv-SE')} kr kvar</span></div>
 <div class="budget-track" aria-label="${pct}% av månadsbudgeten använd"><span style="width:${pct}%"></span></div>
 <div class="budget-foot"><span>Av ${state.settings.monthlyBudget.toLocaleString('sv-SE')} kr</span><span>Veckomål ${state.settings.weeklyBudget.toLocaleString('sv-SE')} kr</span></div>
 ${est.count?`<div class="budget-note">ICA-pris verifierat för ${est.count} av ${est.total} inköpsvaror.</div>`:""}`;
}

function quickSuggestions(){
 const defaults=["Mjölk","Bröd","Ägg","Bananer","Frukt","Yoghurt","Toalettpapper","Kaffe"];
 const names=[...new Set([...Object.keys(state.quickStats||{}),...defaults])];
 return names.sort((a,b)=>(state.quickStats[b]||0)-(state.quickStats[a]||0)).slice(0,6);
}
function addQuickItem(value){
 let v=String(value||"").trim(); if(!v)return;
 state.quick.push(v);
 state.quickStats[v]=(state.quickStats[v]||0)+1;
 localStorage.setItem("quick",JSON.stringify(state.quick));
 localStorage.setItem("quickStats",JSON.stringify(state.quickStats));
 render();
}
function shopView(){
 let items=shopping(),done=items.filter(x=>state.checked.has(x.key)).length,remaining=Math.max(0,items.length-done),suggestions=quickSuggestions();
 return `<section class="page-head shop-page-head"><span class="kicker">Handla</span><h1>Inköpslista</h1><p>${remaining} kvar att köpa${done?` · ${done} klara`:""}</p></section>
 <section class="add-shop-card">
   <label for="quickAddInput">Lägg till vara</label>
   <div class="quick-add-row"><input id="quickAddInput" autocomplete="off" placeholder="T.ex. mjölk eller toalettpapper"><button id="quickAddBtn" aria-label="Lägg till vara">＋</button></div>
   <div class="smart-label">Snabbval</div>
   <div class="smart-chips">${suggestions.map(x=>`<button class="smart-chip" data-quick-add="${esc(x)}">${esc(x)}</button>`).join("")}</div>
 </section>
 <div class="budget-card">${budgetSummary()}<div class="budget-actions"><button class="secondary-btn" id="addGroceryExpense">＋ Registrera butik</button><button class="tertiary-btn" id="addTakeaway">🍕 Hämtmat</button></div></div>
 <div class="list-toolbar"><div><b>Att köpa</b><small>Recept + egna tillägg</small></div><span>${items.length} varor</span></div>
 <section class="shopping-list">${items.length?items.map(x=>`<div class="check-row ${state.checked.has(x.key)?'done':''}"><input type="checkbox" data-check="${esc(x.key)}" ${state.checked.has(x.key)?'checked':''} aria-label="Klar"><label><b>${esc(x.name)}</b>${fmtQty(x)?`<span class="quantity">${esc(fmtQty(x))}</span>`:""}${x.offers.length?`<small class="deal-line">ICA-erbjudande · ${esc(x.offers[0].price||"")}</small>`:""}</label><button class="remove-shop" data-remove-shop="${esc(x.key)}" aria-label="Ta bort">×</button></div>`).join(""):`<div class="empty-state"><b>Listan är tom</b><span>Lägg till något ovan eller skapa en veckoplan.</span></div>`}</section>`;
}
function recipeView(){
 let external=state.recipes.filter(r=>r.external).length;
 return `<section class="page-head"><span class="kicker">Receptbank</span><h1>Hitta något gott</h1><p>${state.recipes.length} recept · ${external} externa · ${state.customRecipes.length} egna</p></section>
 <div class="recipe-actions"><input class="search" id="search" placeholder="Sök på recept eller ingrediens, t.ex. kyckling…"><button class="add-recipe-btn" id="addRecipe">＋ Eget</button></div>
 <div class="filter-row">${["Alla","👍 Gillade","🔥 ICA-match","≤30 min","ICA","Arla","Köket"].map((x,i)=>`<button class="filter ${i===0?'active':''}" data-filter="${x}">${x}</button>`).join("")}</div>
 <div id="recipeList" class="recipe-list">${recipeCards(state.recipes.slice(0,220))}</div>`;
}
function recipeCards(arr){return arr.map(r=>`<div class="card recipe-card" data-id="${esc(recipeKey(r))}">${image(r,"card-image")}<div class="source-badge">${esc(r.source||"Matappen")}${state.liked.has(recipeKey(r))?' · 👍 Gillad':''}</div><div class="meal">${esc(r.name)}</div><div class="row">${meta(r)}</div>${offerBadge(r)}</div>`).join("")}
function wire(){
 document.querySelectorAll("[data-recipeid]").forEach(b=>b.onclick=()=>showRecipe(b.dataset.recipeid));
 document.querySelectorAll(".recipe-card").forEach(c=>c.onclick=()=>showRecipe(c.dataset.id));
 document.querySelectorAll("[data-swap]").forEach(b=>b.onclick=()=>swapMeal(Number(b.dataset.swap)));
 document.querySelectorAll("[data-goto]").forEach(b=>b.onclick=()=>{state.view=b.dataset.goto;document.querySelectorAll(".nav-btn").forEach(x=>x.classList.toggle("active",x.dataset.view===state.view));render();scrollTo(0,0)});
 document.querySelectorAll("[data-check]").forEach(c=>c.onchange=()=>{c.checked?state.checked.add(c.dataset.check):state.checked.delete(c.dataset.check);localStorage.setItem("checked",JSON.stringify([...state.checked]));render()});
 document.querySelectorAll("[data-remove-shop]").forEach(b=>b.onclick=()=>{state.hiddenShop.add(b.dataset.removeShop);save();render()});
 document.querySelectorAll("[data-quick-add]").forEach(b=>b.onclick=()=>addQuickItem(b.dataset.quickAdd));
 if($("#quickAddBtn"))$("#quickAddBtn").onclick=()=>{addQuickItem($("#quickAddInput").value);};
 if($("#quickAddInput"))$("#quickAddInput").onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();addQuickItem(e.currentTarget.value)}};
 if($("#addRecipe"))$("#addRecipe").onclick=addOwnRecipe;
 if($("#search"))$("#search").oninput=filterRecipes;
 if($("#addGroceryExpense"))$("#addGroceryExpense").onclick=()=>addExpense("Matbutik");
 if($("#addTakeaway"))$("#addTakeaway").onclick=()=>addExpense("Hämtmat");
 document.querySelectorAll("[data-filter]").forEach(b=>b.onclick=()=>{document.querySelectorAll("[data-filter]").forEach(x=>x.classList.remove("active"));b.classList.add("active");state.filter=b.dataset.filter;filterRecipes()});
}
function swapMeal(i){let cur=state.week[i].recipe,counts={};state.week.forEach((p,j)=>{if(j!==i)counts[mainGroup(p.recipe)]=(counts[mainGroup(p.recipe)]||0)+1});let pool=state.recipes.filter(r=>recipeKey(r)!==recipeKey(cur)&&!state.disliked.has(recipeKey(r))&&!state.week.some((p,j)=>j!==i&&recipeKey(p.recipe)===recipeKey(r)));pool.sort((a,b)=>baseScore(b,i,counts)-baseScore(a,i,counts));if(pool[0])state.week[i]={...state.week[i],recipe:pool[0]};render()}
function showRecipe(id){let r=state.recipes.find(x=>recipeKey(x)===id);if(!r)return;let key=recipeKey(r),body=`${image(r,"sheet-image")}<div class="source-badge">${esc(r.source||"Matappen")}</div><h3>${esc(r.name)}</h3><div class="row">${meta(r)}</div>${offerBadge(r)}<div class="taste-actions"><button class="${state.liked.has(key)?'taste-on':''}" id="likeRecipe">👍 Den här gillar vi</button><button class="${state.disliked.has(key)?'taste-bad':''}" id="dislikeRecipe">👎 Inte för oss</button></div>`;if((r.ingredients||[]).length)body+=`<h4>Ingredienser</h4>${r.ingredients.map(x=>`<div class="ingredient">${esc(x)}</div>`).join("")}`;if(r.external&&r.url)body+=`<a href="${esc(r.url)}" target="_blank" rel="noopener" class="wide-btn link-btn">Öppna hos ${esc(r.source)} ↗</a>`;else if(r.steps)body+=`<h4>Gör så här</h4>${r.steps.map((s,i)=>`<div class="step"><b>${i+1}.</b> ${esc(s)}</div>`).join("")}`;showSheet(body);setTimeout(()=>{$("#likeRecipe").onclick=()=>{state.liked.add(key);state.disliked.delete(key);saveTaste();buildWeek();closeSheet();render()};$("#dislikeRecipe").onclick=()=>{state.disliked.add(key);state.liked.delete(key);saveTaste();buildWeek();closeSheet();render()}},10)}
function saveTaste(){localStorage.setItem("likedV24",JSON.stringify([...state.liked]));localStorage.setItem("dislikedV24",JSON.stringify([...state.disliked]))}
function filterRecipes(){let q=$("#search").value.toLowerCase().trim(),f=state.filter,arr=state.recipes.filter(r=>(r.name+" "+(r.ingredients||[]).join(" ")+" "+(r.tags||[]).join(" ")).toLowerCase().includes(q));if(f==="≤30 min")arr=arr.filter(r=>mins(r)&&mins(r)<=30);if(["ICA","Arla","Köket"].includes(f))arr=arr.filter(r=>r.source===f);if(f==="👍 Gillade")arr=arr.filter(r=>state.liked.has(recipeKey(r)));if(f==="🔥 ICA-match")arr=arr.filter(r=>offerMatches(r).length);$("#recipeList").innerHTML=recipeCards(arr.slice(0,220));document.querySelectorAll(".recipe-card").forEach(c=>c.onclick=()=>showRecipe(c.dataset.id))}
function addOwnRecipe(){showSheet(`<h3>＋ Eget recept</h3><label class="form-label">Namn</label><input class="search" id="ownName"><div class="form-grid"><div><label class="form-label">Portioner</label><input class="search" id="ownPortions" value="4"></div><div><label class="form-label">Tid, min</label><input class="search" id="ownMinutes"></div></div><label class="form-label">Ingredienser – en per rad</label><textarea class="recipe-textarea" id="ownIngredients"></textarea><label class="form-label">Gör så här</label><textarea class="recipe-textarea" id="ownSteps"></textarea><button class="wide-btn" id="saveOwnRecipe">Spara recept</button>`);setTimeout(()=>{$("#saveOwnRecipe").onclick=()=>{let name=$("#ownName").value.trim(),ingredients=$("#ownIngredients").value.split(/\n/).map(x=>x.trim()).filter(Boolean);if(!name||!ingredients.length)return;let r={id:"own-"+Date.now(),name,source:"Eget recept",external:false,ingredients,steps:$("#ownSteps").value.split(/\n/).filter(Boolean),minutes:Number($("#ownMinutes").value)||null,portions:Number($("#ownPortions").value)||4,tags:["eget"]};state.customRecipes.unshift(r);localStorage.setItem("customRecipes",JSON.stringify(state.customRecipes));state.recipes.unshift(r);buildWeek();closeSheet();render()}},10)}
function addExpense(type){showSheet(`<h3>${type==='Hämtmat'?'🍕 Hämtmat':'🛒 Matbutik'}</h3><input class="search" id="expenseAmount" inputmode="decimal" placeholder="Belopp i kr"><button class="wide-btn" id="saveExpense">Spara</button>`);setTimeout(()=>{$("#saveExpense").onclick=()=>{let amount=Number($("#expenseAmount").value.replace(",","."));if(!amount)return;state.expenses.push({date:new Date().toISOString().slice(0,10),type,amount});save();closeSheet();render()}},10)}
function customAdd(){
 showSheet(`<h3>Lägg till vara</h3><input class="search" id="customInput" placeholder="Vad behöver ni?"><button class="wide-btn" id="saveCustom">Lägg till</button>`);
 setTimeout(()=>{$("#saveCustom").onclick=()=>{addQuickItem($("#customInput").value);closeSheet()}},10)
}
function showInfo(){
 showSheet(`<div class="sheet-kicker">Inställningar</div><h3>Matappen v25</h3><p class="sheet-intro">Planeringen tar hänsyn till barn/vuxen-dagar, portionsmål, variation, ICA-erbjudanden och er budget.</p>
 <label class="form-label">Torsdagen är</label><select class="search" id="handover"><option value="arrival" ${state.settings.handover==='arrival'?'selected':''}>ankomstdag varannan vecka</option><option value="departure" ${state.settings.handover==='departure'?'selected':''}>avresedag varannan vecka</option></select>
 <div class="form-grid"><div><label class="form-label">Veckomål</label><input class="search" id="weeklyBudget" inputmode="numeric" value="${state.settings.weeklyBudget}"></div><div><label class="form-label">Månadsbudget</label><input class="search" id="monthlyBudget" inputmode="numeric" value="${state.settings.monthlyBudget}"></div></div>
 <button class="wide-btn" id="saveSettings">Spara inställningar</button>
 <div class="settings-note">${state.offerStatus==='live'?`ICA: ${state.offers.length} verifierade erbjudanden`:"ICA-erbjudanden är inte verifierade just nu"}</div>`);
 setTimeout(()=>{$("#saveSettings").onclick=()=>{state.settings.handover=$("#handover").value;state.settings.weeklyBudget=Number($("#weeklyBudget").value)||1600;state.settings.monthlyBudget=Number($("#monthlyBudget").value)||12000;save();buildWeek();closeSheet();render()}},10)
}
function showSheet(html){$("#sheet").innerHTML=html;$("#sheetBackdrop").classList.remove("hidden");$("#sheet").classList.remove("hidden");$("#sheetBackdrop").onclick=closeSheet}function closeSheet(){$("#sheetBackdrop").classList.add("hidden");$("#sheet").classList.add("hidden")}
init();

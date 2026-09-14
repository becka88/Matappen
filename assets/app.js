let state={
 recipes:[],offers:[],offerStatus:"waiting",view:"today",week:[],
 liked:new Set(JSON.parse(localStorage.getItem("likedV24")||"[]")),
 disliked:new Set(JSON.parse(localStorage.getItem("dislikedV24")||"[]")),
 checked:new Set(JSON.parse(localStorage.getItem("checked")||"[]")),
 quick:JSON.parse(localStorage.getItem("quick")||"[]"),quickStats:JSON.parse(localStorage.getItem("quickStats")||"{}"),
 filter:"Alla",customRecipes:JSON.parse(localStorage.getItem("customRecipes")||"[]"),
 hiddenShop:new Set(JSON.parse(localStorage.getItem("hiddenShopV24")||"[]")),
 settings:JSON.parse(localStorage.getItem("familySettingsV24")||'{"handover":"arrival","handoverDay":4,"weeklyBudget":1600,"monthlyBudget":12000}'),
 expenses:JSON.parse(localStorage.getItem("expensesV24")||"[]"),
 offerCart:JSON.parse(localStorage.getItem("offerCartV28")||"[]"),
 prices:[],priceStatus:"unavailable",priceUpdated:null
};
const $=s=>document.querySelector(s), esc=s=>String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]));
const days=["Torsdag","Fredag","Lördag","Söndag","Måndag","Tisdag","Onsdag"];
const canon=s=>String(s||"").toLowerCase().replace(/[,:()]/g," ").replace(/filéer/g,"filé").replace(/kycklingbröst/g,"kycklingfilé").replace(/färsen/g,"färs").replace(/\s+/g," ").trim();
const recipeKey=r=>String(r.id||((r.source||"")+":"+(r.name||"")));
const mins=r=>r.minutes??null;
function isoWeek(d=new Date()){let x=new Date(Date.UTC(d.getFullYear(),d.getMonth(),d.getDate()));x.setUTCDate(x.getUTCDate()+4-(x.getUTCDay()||7));let y=new Date(Date.UTC(x.getUTCFullYear(),0,1));return Math.ceil((((x-y)/86400000)+1)/7)}

function localDateKey(d){let y=d.getFullYear(),m=String(d.getMonth()+1).padStart(2,"0"),day=String(d.getDate()).padStart(2,"0");return `${y}-${m}-${day}`}
function parseLocalDate(s){let [y,m,d]=String(s||"").split("-").map(Number);return new Date(y,m-1,d,12)}
function matWeekStart(date=new Date()){let d=new Date(date.getFullYear(),date.getMonth(),date.getDate(),12),diff=(d.getDay()-4+7)%7;d.setDate(d.getDate()-diff);return d}
function addDays(d,n){let x=new Date(d);x.setDate(x.getDate()+n);return x}
function dayIndexInMatWeek(date=new Date()){return (date.getDay()-4+7)%7}
function shortDate(d){return d.toLocaleDateString("sv-SE",{day:"numeric",month:"short"}).replace(".","")}
function matWeekLabel(){let s=matWeekStart(),e=addDays(s,6);return `${shortDate(s)}–${shortDate(e)}`}
function ensureAnchor(){
 if(!state.settings.anchorThursday){
   state.settings.anchorThursday=localDateKey(matWeekStart());
   state.settings.handover=state.settings.handover||"arrival";
   save();
 }
}
function currentHandoverType(){
 ensureAnchor();
 let start=matWeekStart(),anchor=parseLocalDate(state.settings.anchorThursday);
 let weeks=Math.round((start-anchor)/604800000),same=((weeks%2)+2)%2===0;
 return same?(state.settings.handover||"arrival"):((state.settings.handover||"arrival")==="arrival"?"departure":"arrival");
}
function weekKey(){return `THU-${localDateKey(matWeekStart())}`}
function save(){
 localStorage.setItem("familySettingsV24",JSON.stringify(state.settings));
 localStorage.setItem("expensesV24",JSON.stringify(state.expenses));
 localStorage.setItem("hiddenShopV24",JSON.stringify([...state.hiddenShop]));
 localStorage.setItem("offerCartV28",JSON.stringify(state.offerCart));
}
function isKidsDay(i){return currentHandoverType()==="arrival"}
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
function mainGroup(r){
 const t=canon((r.name||"")+" "+(r.ingredients||[]).join(" "));
 for(const [g,re] of [
  ["korv",/\b(?:falukorv|middagskorv|korv)\b/],
  ["kyckling",/\bkyckling\b/],["lax",/\blax\b/],["fisk",/\b(?:torsk|sej|fisk)\b/],
  ["färs",/\b(?:köttfärs|nötfärs|blandfärs|färs)\b/],["fläsk",/\b(?:fläsk|kotlett|fläskfilé)\b/],
  ["vegetariskt",/\b(?:linser|bönor|tofu|halloumi|vegetar)\b/]
 ]) if(re.test(t))return g;
 return "annat"
}
function baseScore(r,i,counts){
 let s=0,key=recipeKey(r),m=mins(r),kids=isKidsDay(i),g=mainGroup(r),matches=offerMatches(r),repeat=counts[g]||0;
 if(state.liked.has(key))s+=28;
 if(state.disliked.has(key))return-9999;
 if(repeat>=2 && g!=="annat")return-9998;
 if(matches.length){
   s+=Math.min(52,28+matches.reduce((n,x)=>n+x.weight,0)*4);
   if(repeat===1 && g!=="annat")s-=10;
 }else if(repeat){
   s-=g==="annat"?7:38*repeat;
 }
 if(kids){
   if((r.tags||[]).includes("barnvänlig")||/taco|pasta|köttbull|pannkak|mild/i.test(r.name))s+=12;
   if(/stark|chili/i.test(r.name))s-=12;
 }else if(/curry|chili|gryta|asiat/i.test(r.name))s+=5;
 if(i<5&&m&&m<=35)s+=7;
 if(i===1&&/taco|pizza|burg|quesadilla/i.test(r.name))s+=9;
 return s
}
function buildWeek(){
 ensureAnchor();
 let used=new Set(),counts={},week=[],start=matWeekStart();

 for(let i=0;i<7;i++){
   let all=state.recipes.filter(r=>!used.has(recipeKey(r))&&!state.disliked.has(recipeKey(r)));

   // Max två middagar med samma tydliga huvudråvara.
   // Om receptbanken är liten väljer vi hellre en annan huvudgrupp än fem kycklingrätter.
   let allowed=all.filter(r=>{
     let g=mainGroup(r);
     return g==="annat" || (counts[g]||0)<2;
   });

   // Sprid även "annat"-rätter genom titel/huvudord så samma typ inte tar över veckan.
   let pool=allowed;

   pool.sort((a,b)=>{
     let ga=mainGroup(a),gb=mainGroup(b);
     let sa=baseScore(a,i,counts),sb=baseScore(b,i,counts);
     if((counts[ga]||0)!==(counts[gb]||0)) {
       // Vid ungefär likvärdiga recept gynnas den huvudgrupp som använts minst.
       let diff=(counts[gb]||0)-(counts[ga]||0);
       if(Math.abs(sa-sb)<25)return diff;
     }
     return sb-sa;
   });

   let r=pool[0];
   if(!r)continue;

   used.add(recipeKey(r));
   let g=mainGroup(r);
   counts[g]=(counts[g]||0)+1;

   let date=addDays(start,i);
   week.push({
     day:days[i],date:localDateKey(date),dateLabel:shortDate(date),
     recipe:r,kids:isKidsDay(i),portions:targetPortions(i)
   });
 }
 state.week=week;
 resetHiddenForWeek();
}
function resetHiddenForWeek(){const k="hiddenShopWeekV24";if(localStorage.getItem(k)!==weekKey()){state.hiddenShop.clear();localStorage.setItem(k,weekKey());localStorage.setItem("hiddenShopV24","[]")}}
function approvedSourceRecipe(r){
 if(!r||r.external!==true||!["ICA","Arla","Köket"].includes(r.source)||!Array.isArray(r.ingredients)||r.ingredients.length<2||!r.url)return false;
 try{let h=new URL(r.url).hostname.replace(/^www\./,"");return (r.source==="ICA"&&h==="ica.se")||(r.source==="Arla"&&h==="arla.se")||(r.source==="Köket"&&h==="koket.se")}catch{return false}
}
async function init(){try{const[rr,oo,pp]=await Promise.all([fetch("./recipes.json?"+Date.now()).then(r=>r.json()),fetch("./offers.json?"+Date.now()).then(r=>r.ok?r.json():({status:"unavailable",offers:[]})),fetch("./prices.json?"+Date.now()).then(r=>r.ok?r.json():({status:"unavailable",products:[]})).catch(()=>({status:"unavailable",products:[]}))]);let sourced=Array.isArray(rr)?rr.filter(approvedSourceRecipe):[];state.recipes=[...state.customRecipes,...sourced];state.offerStatus=oo.status||"unavailable";state.offers=oo.offers||[];state.offerPageCount=oo.page_offer_count||state.offers.length;state.offerCoverage=oo.coverage||"";state.priceStatus=pp.status||"unavailable";state.prices=pp.products||[];state.priceUpdated=pp.updated_at||null;buildWeek();render();bindNav()}catch(e){$("#view").innerHTML='<div class="card">Kunde inte läsa Matappens data just nu.</div>'}}
function bindNav(){document.querySelectorAll(".nav-btn").forEach(b=>b.onclick=()=>{state.view=b.dataset.view;document.querySelectorAll(".nav-btn").forEach(x=>x.classList.toggle("active",x===b));render();scrollTo(0,0)});$("#profileBtn").onclick=showInfo}
function image(r,cls="recipe-image"){return r.image?`<img class="${cls}" src="${esc(r.image)}" alt="" loading="lazy" referrerpolicy="no-referrer">`:""}
function meta(r){let a=[];if(mins(r))a.push(`⏱ ${mins(r)} min`);if(r.external)a.push(`↗ ${r.source}`);return a.map(x=>`<span class="soft-chip">${esc(x)}</span>`).join("")}
function offerBadge(r){let m=offerMatches(r);if(!m.length)return"";return `<div class="offer">🔥 Passar veckans erbjudande: ${m.map(x=>`<b>${esc(x.offer.name)}</b>`).join(" + ")}</div>`}
function familyChip(p){return `<span class="family-chip ${p.kids?'kids':'adult'}">${p.kids?'👨‍👩‍👧‍👦 Barnen hemma':'🌶️ Vuxenkväll'} · ${p.portions} port</span>`}
function render(){if(state.view==="today")$("#view").innerHTML=todayView();if(state.view==="week")$("#view").innerHTML=weekView();if(state.view==="shop")$("#view").innerHTML=shopView();if(state.view==="recipes")$("#view").innerHTML=recipeView();if(state.view==="offers")$("#view").innerHTML=offersView();wire()}
function todayView(){
 if(!state.week.length)return `<section class="page-head"><span class="kicker">Matappen</span><h1>Recepten uppdateras</h1><p>Receptbanken innehåller bara recept från ICA, Arla och Köket.</p></section><div class="card empty-state"><b>Inga källrecept inlästa ännu</b><span>Kör “Uppdatera Matappen” i GitHub Actions så hämtas recepten.</span></div>`;
 let i=dayIndexInMatWeek(),p=state.week[i]||state.week[0],t=state.week[(i+1)%7]||state.week[0],remaining=shopping().filter(x=>!state.checked.has(x.key)).length,hand=currentHandoverType();
 return `<section class="cycle-strip"><b>${matWeekLabel()}</b><span>${hand==="arrival"?"👨‍👩‍👧‍👦 Barnvecka från torsdag":"🌶️ Vuxenvecka från torsdag"}</span></section>
 <section class="hero-card">${image(p.recipe,"hero-image")}
 <div class="hero-label">${p.day} ${p.dateLabel} · dagens middag</div>
 <div class="hero-title">${esc(p.recipe.name)}</div>
 <div class="meta">${familyChip(p)}${meta(p.recipe)}</div>${offerBadge(p.recipe)}
 <div class="hero-actions"><button class="light" data-recipeid="${esc(recipeKey(p.recipe))}">Visa recept</button><button class="ghost" data-swap="${i}">↻ Byt rätt</button></div></section>
 ${featuredOffers()}
 <div class="home-glance"><button class="glance-card" data-goto="shop"><span class="glance-icon">🛒</span><span><b>${remaining} saker kvar</b><small>Öppna inköpslistan</small></span><span class="chev">›</span></button></div>
 <div class="budget-card">${budgetSummary()}</div>
 ${state.offerStatus==="live"?`<div class="home-offer-line">🔥 ${state.offers.length} ICA-erbjudanden inne</div>`:""}
 <section class="section"><div class="section-head"><div><h2>I morgon</h2><div class="muted">Nästa middag i planen</div></div></div><div class="card mini-meal">${image(t.recipe,"thumb")}<div><div class="day">${t.day} ${t.dateLabel}</div><div class="meal">${esc(t.recipe.name)}</div>${familyChip(t)}${offerBadge(t.recipe)}</div></div></section>`;
}
function weekView(){
 if(!state.week.length)return `<section class="page-head"><span class="kicker">Matvecka · torsdag–onsdag</span><h1>${matWeekLabel()}</h1><p>Recepten hämtas från ICA, Arla och Köket.</p></section><div class="card empty-state"><b>Ingen veckoplan ännu</b><span>Receptbanken väntar på nästa uppdatering.</span></div>`;
 let hand=currentHandoverType();
 return `<section class="page-head"><span class="kicker">Matvecka · torsdag–onsdag</span><h1>${matWeekLabel()}</h1><p>${hand==="arrival"?"Barnen kommer på torsdag.":"Barnen lämnas på torsdag."}</p></section>
 ${featuredOffers()}
 <section class="week-list">${state.week.map((p,i)=>`<article class="card week-card">${image(p.recipe,"thumb")}<div class="week-main"><div class="day">${p.day} · ${p.dateLabel}</div><div class="meal">${esc(p.recipe.name)}</div>${familyChip(p)}<div class="row">${meta(p.recipe)}</div>${offerBadge(p.recipe)}<div class="week-actions"><button class="secondary-btn" data-recipeid="${esc(recipeKey(p.recipe))}">Visa recept</button><button class="tertiary-btn" data-swap="${i}">↻ Byt</button></div></div></article>`).join("")}</section>`;
}
function parseIngredient(line){let s=String(line||"").trim(),m=s.match(/^(.+?):\s*([\d.,½¼¾⅓⅔]+)\s*([a-zA-ZåäöÅÄÖ]+)?/);if(m)return{name:m[1].trim(),qty:m[2],unit:m[3]||""};m=s.match(/^([\d.,½¼¾⅓⅔]+)\s*([a-zA-ZåäöÅÄÖ]+)?\s+(.+)$/);if(m)return{name:m[3].trim(),qty:m[1],unit:m[2]||""};return{name:s,qty:"",unit:""}}
function num(s){if(!s)return null;const f={"½":.5,"¼":.25,"¾":.75,"⅓":1/3,"⅔":2/3};if(f[s])return f[s];let n=parseFloat(String(s).replace(",","."));return Number.isFinite(n)?n:null}
function unitKey(u){
 let x=canon(u);
 if(/^(?:st|styck|stycken|ägg|äggula|äggulor)$/.test(x))return "st";
 return x
}
function shopName(s){
 let x=canon(s).replace(/\([^)]*\)/g," ").replace(/[;,].*$/,"").replace(/\s+/g," ").trim();
 x=x.replace(/^(?:ca|cirka)\s+/,"")
    .replace(/^(?:smält|rumstempererat|rumstempererad|kall|kallt|varm|varmt|mjuk|mjukt|hackad|hackat|finhackad|finhackat|grovhackad|grovhackat|riven|rivet|skivad|skivat|pressad|pressat|skalad|skalat|kokt|kokta|stekt|stekta|färsk|färska|fryst|frysta)\s+/,"")
    .replace(/\s+(?:efter smak|till servering|till garnering|för stekning|att steka i|valfritt|valfri|gärna).*$/,"").trim();
 const rules=[
  [/^(?:salt\s*(?:och|&)\s*(?:svart)?peppar|salt\/(?:svart)?peppar)$/,"salt & peppar"],
  [/^(?:svartpeppar|vitpeppar|peppar|nymalen svartpeppar|malen svartpeppar)$/,"peppar"],
  [/^(?:flingsalt|havssalt|fint salt|salt)$/,"salt"],
  [/^(?:äggula|äggulor|äggvita|äggvitor|ägg)$/,"ägg"],
  [/^(?:gul lök|gula lökar|lökar|lök)$/,"gul lök"],
  [/^(?:röd lök|rödlök|röda lökar)$/,"röd lök"],
  [/^(?:vitlöksklyfta|vitlöksklyftor|vitlök)$/,"vitlök"],
  [/^(?:smör|matfett|smält smör|mjukt smör)$/,"smör"],
  [/^(?:vispgrädde|matlagningsgrädde|mellangrädde|grädde)$/,"grädde"],
  [/^(?:creme fraiche|crème fraiche)$/,"crème fraiche"],
  [/^(?:riven ost|gratängost|pizzaost|ost)$/,"ost"],
  [/^(?:krossad tomat|krossade tomater)$/,"krossade tomater"],
  [/^(?:passerad tomat|passerade tomater)$/,"passerade tomater"],
  [/^(?:majskorn|majs)$/,"majs"],
  [/^(?:strösocker|socker)$/,"socker"],
  [/^(?:olivolja|extra virgin olivolja)$/,"olivolja"],
  [/^(?:matolja|neutral olja|rapsolja)$/,"rapsolja"],
  [/^(?:vetemjöl|mjöl)$/,"vetemjöl"],
  [/^(?:kycklingfilé|kycklingfile|kycklingfiléer|kycklingfileer)$/,"kycklingfilé"],
  [/^(?:spagetti|spaghetti)$/,"spaghetti"],
  [/^(?:makaron|makaroner)$/,"makaroner"]
 ];
 for(const [re,to] of rules)if(re.test(x))return to;
 const plurals={"morötter":"morot","tomater":"tomat","paprikor":"paprika","champinjoner":"champinjon","citroner":"citron","bananer":"banan","äpplen":"äpple","potatisar":"potatis"};
 return plurals[x]||x
}
function expandIngredient(line){let raw=String(line||"").trim(),c=canon(raw);if(!raw||/^(?:till servering|servering|garnering|sås|dressing|marinad)\s*:?\s*$/i.test(raw))return[];if(/\b(?:se länk|se recept|enligt recept|recept finns)\b/.test(c))return[];return[raw]}

function toBaseAmount(qty,unit,name){
 let q=Number(qty); if(!Number.isFinite(q))return null;
 let u=canon(unit),n=canon(name);
 if(u==="kg")return {kind:"g",amount:q*1000};
 if(u==="g")return {kind:"g",amount:q};
 if(u==="l"||u==="liter")return {kind:"ml",amount:q*1000};
 if(u==="dl")return {kind:"ml",amount:q*100};
 if(u==="cl")return {kind:"ml",amount:q*10};
 if(u==="ml")return {kind:"ml",amount:q};
 if(u==="msk"){
   if(/^(?:smör|matfett)$/.test(n))return {kind:"g",amount:q*15};
   if(/pulver|krydda|paprika|curry|oregano|timjan|kanel|chili|vitlökspulver/.test(n))return {kind:"g",amount:q*7};
   return {kind:"ml",amount:q*15};
 }
 if(u==="tsk"){
   if(/^(?:smör|matfett)$/.test(n))return {kind:"g",amount:q*5};
   if(/pulver|krydda|paprika|curry|oregano|timjan|kanel|chili|vitlökspulver/.test(n))return {kind:"g",amount:q*2.5};
   return {kind:"ml",amount:q*5};
 }
 if(u==="krm")return {kind:"g",amount:q*0.7};
 if(u==="st"||!u)return {kind:"st",amount:q};
 return {kind:u,amount:q}
}
function roundPacks(amount,size){return Math.max(1,Math.ceil((amount||0)/size))}
function purchasePlan(item){
 let alreadyBase=item.parts&&item.parts.length&&["g","ml","st"].includes(item.unit);
 let b=alreadyBase?{kind:item.unit,amount:item.qty}:toBaseAmount(item.qty,item.unit,item.name),amount=b?.amount??null,kind=b?.kind||"",n=canon(item.name);
 if(/^(?:salt|peppar)$/.test(n))return {label:"1 förpackning",need:1,kind:"st"};
 if(item.mixedParts?.length)return {label:"1 förpackning",need:1,kind:"st"};
 if(n==="ägg")return {label:`minst ${Math.max(1,Math.ceil(amount||1))} ägg`,need:Math.max(1,Math.ceil(amount||1)),kind:"st"};
 if(/pulver|krydda|paprika|curry|oregano|timjan|kanel|chili|spiskummin|rosmarin|basilika|gurkmeja/.test(n))return {label:"1 burk/påse",need:amount||1,kind:"g"};
 if(kind==="g")return {label:`minst ${Math.ceil(amount||1)} g`,need:amount||1,kind:"g"};
 if(kind==="ml")return {label:`minst ${Math.ceil(amount||1)} ml`,need:amount||1,kind:"ml"};
 if(kind==="st")return {label:`minst ${Math.ceil(amount||1)} st`,need:amount||1,kind:"st"};
 return {label:"1 förpackning",need:1,kind:"st"}
}

function productPack(p){
 let s=canon(`${p.pack||""} ${p.name||""}`),m,total;
 if((m=s.match(/(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*(kg|g|l|dl|cl|ml)\b/))){
   let mult=Number(m[1]),v=Number(m[2].replace(",",".")),u=m[3];
   if(u==="kg")return {kind:"g",amount:mult*v*1000};
   if(u==="g")return {kind:"g",amount:mult*v};
   if(u==="l")return {kind:"ml",amount:mult*v*1000};
   if(u==="dl")return {kind:"ml",amount:mult*v*100};
   if(u==="cl")return {kind:"ml",amount:mult*v*10};
   if(u==="ml")return {kind:"ml",amount:mult*v};
 }
 if((m=s.match(/(\d+(?:[.,]\d+)?)\s*kg\b/)))return {kind:"g",amount:Number(m[1].replace(",","."))*1000};
 if((m=s.match(/(\d+(?:[.,]\d+)?)\s*g\b/)))return {kind:"g",amount:Number(m[1].replace(",","."))};
 if((m=s.match(/(\d+(?:[.,]\d+)?)\s*(?:l|liter)\b/)))return {kind:"ml",amount:Number(m[1].replace(",","."))*1000};
 if((m=s.match(/(\d+(?:[.,]\d+)?)\s*dl\b/)))return {kind:"ml",amount:Number(m[1].replace(",","."))*100};
 if((m=s.match(/(\d+(?:[.,]\d+)?)\s*cl\b/)))return {kind:"ml",amount:Number(m[1].replace(",","."))*10};
 if((m=s.match(/(\d+(?:[.,]\d+)?)\s*ml\b/)))return {kind:"ml",amount:Number(m[1].replace(",","."))};
 if((m=s.match(/(\d+)\s*(?:-p|p\b|pack|st\b)/)))return {kind:"st",amount:Number(m[1])};
 return null
}
function itemTokens(name){return canon(name).split(/\s+/).filter(x=>x.length>2&&!["färsk","fryst","hackad","riven","skivad","finhackad"].includes(x))}

function priceSearchName(name){
 let n=shopName(name);
 const aliases=[
  [/creme fraiche|crème fraiche/,"crème fraiche"],
  [/matlagningsgrädde|vispgrädde|grädde/,"grädde"],
  [/gul lök|röd lök|silverlök/,"lök"],
  [/morötter|morot/,"morot"],
  [/krossade tomater|passerade tomater/,"tomater"],
  [/nötfärs|blandfärs|köttfärs/,"köttfärs"],
  [/kycklingfilé|kycklinglårfilé|kycklingbröst/,"kyckling"],
  [/spaghetti|penne|makaroner/,"pasta"],
  [/vitlöksklyftor|vitlöksklyfta/,"vitlök"],
  [/äggulor|äggula/,"ägg"]
 ];
 for(const [re,to] of aliases)if(re.test(n))return to;
 return n.replace(/\b(färsk|fryst|hackad|finhackad|riven|skivad|ekologisk|eko)\b/g," ").replace(/\s+/g," ").trim()
}
function tokenScore(a,b){
 let A=new Set(canon(a).split(/\s+/).filter(x=>x.length>2)),B=new Set(canon(b).split(/\s+/).filter(x=>x.length>2));
 if(!A.size||!B.size)return 0;
 let hit=0;A.forEach(x=>{if(B.has(x))hit++});
 return hit/A.size
}
function realProductForItem(item){
 let wanted=priceSearchName(item.name),plan=purchasePlan(item);
 let candidates=state.prices.map(p=>{
   let queryText=Array.isArray(p.queries)?p.queries.join(" "):(p.query||"");
   let productText=`${p.name||""} ${p.brand||""}`;
   let queryScore=Math.max(...String(queryText).split("|").map(q=>tokenScore(wanted,q)),0);
   let nameScore=tokenScore(wanted,productText);
   let exact=canon(queryText).includes(canon(wanted))||canon(productText).includes(canon(wanted));
   let relevance=Math.max(queryScore,nameScore)+(exact?0.45:0);
   if(relevance<0.66)return null;
   let pack=productPack(p),packs=1;
   if(pack&&pack.kind===plan.kind&&Number(plan.need)>0)packs=Math.max(1,Math.ceil(plan.need/pack.amount));
   let price=Number(p.promotion_price||p.price);
   let cost=price*packs;
   if(!Number.isFinite(cost)||cost<=0)return null;
   let ownBrand=/(^|\s)ica(\s|$)/.test(canon(`${p.brand||""} ${p.name||""}`))?0.08:0;
   let available=p.available===false?-1:0;
   return {...p,packs,cost,relevance:relevance+ownBrand+available,packParsed:pack}
 }).filter(Boolean);
 candidates.sort((a,b)=>b.relevance-a.relevance||a.cost-b.cost);
 return candidates[0]||null
}
function bestOfferPriceForItem(item){
 if(state.offerStatus!=="live")return null;
 let match=(item.offers||[])[0];
 if(!match)return null;
 let p=offerCost(match); if(!p)return null;
 let plan=purchasePlan(item);
 if(p.type==="bundle")return {cost:Math.ceil((plan.packs||1)/p.qty)*p.cost,label:match.price,source:"ICA-erbjudande"};
 if(p.type==="st")return {cost:(plan.packs||1)*p.cost,label:match.price,source:"ICA-erbjudande"};
 return null
}

function nonPurchaseIngredient(name){
 let n=canon(name).replace(/\([^)]*\)/g," ").replace(/\s+/g," ").trim();
 if(!n)return true;
 const exact=new Set([
  "vatten","kranvatten","kokvatten","pastavatten","pastakokvatten",
  "vatten från pastakoket","vatten från koket","kokvatten från pastan",
  "isbitar","is","krossad is"
 ]);
 if(exact.has(n))return true;
 if(/^(?:kallt |varmt |ljummet |kokande |iskallt )?(?:kran)?vatten\b/.test(n))return true;
 if(/\b(?:pasta)?kokvatten\b/.test(n))return true;
 if(/\bvatten\s+från\s+(?:pasta)?koket\b/.test(n))return true;
 if(/\bkokvatten\s+från\s+pastan\b/.test(n))return true;
 if(/^(?:till servering|servering|garnering|tillbehör|sås|dressing|marinad)\s*:?\s*$/.test(n))return true;
 if(/^(?:efter smak|smaka av|för servering)\s*$/.test(n))return true;
 return false;
}

function cleanIngredientNameForShopping(name){
 let n=shopName(name);
 n=n
  .replace(/\s+(?:till|för)\s+(?:stekning|stekning och servering|servering|garnering|formen|bakning)\s*$/,"")
  .replace(/\s+(?:efter smak|vid behov|om så önskas|valfritt|valfri)\s*$/,"")
  .replace(/\s+/g," ")
  .trim();
 return n;
}
function shopping(){
 let map=new Map(),never=new Set(["vatten","kranvatten","kokvatten","pastavatten","pastakokvatten","vatten från pastakoket","vatten från koket"]);
 const add=(x,factor=1,extra={})=>{
   if(nonPurchaseIngredient(x.name))return;
   let key=cleanIngredientNameForShopping(x.name),u=unitKey(x.unit),n=num(x.qty);
   if(!key||never.has(key)||nonPurchaseIngredient(key))return;
   if(key==="salt & peppar"&&!extra.offerItem){
     add({...x,name:"salt"},factor,extra);
     add({...x,name:"peppar"},factor,extra);
     return;
   }

   // Vanliga receptvaror slås alltid ihop till en rad.
   // Explicit tillagda erbjudanden behåller egen rad.
   let k=extra.key||key,item=map.get(k);
   if(!item){
     item={key:k,name:key,unit:"",qty:null,parts:[],offers:[],plannedCost:null,offerItem:false};
     map.set(k,item)
   }

   if(n!==null){
     item.parts.push({qty:n*factor,unit:u});
   }
   Object.assign(item,extra);
 };

 state.week.forEach(p=>{
   let factor=p.portions/Number(p.recipe.portions||4);
   (p.recipe.ingredients||[]).forEach(line=>expandIngredient(line).forEach(x=>add(parseIngredient(x),factor)));
 });

 state.quick.forEach(x=>add({name:x,qty:"",unit:""}));

 state.offerCart.forEach(x=>add({name:x.name,qty:x.dealQty||1,unit:"st"},1,{
   key:"offer:"+x.id,name:shopName(x.name),plannedCost:x.plannedCost,offerItem:true,offers:[x]
 }));

 for(const item of map.values()){
   if(!item.offerItem && item.parts.length){
     const bases=item.parts.map(p=>toBaseAmount(p.qty,p.unit,item.name)).filter(Boolean);
     const kinds=[...new Set(bases.map(b=>b.kind))];

     if(kinds.length===1){
       item.unit=kinds[0];
       item.qty=bases.reduce((sum,b)=>sum+b.amount,0);
     }else{
       // Om källrecepten använder inkompatibla mått för samma vara ska den
       // ändå bara synas en gång. Behåll delarna för en tydlig köptext.
       item.unit="";
       item.qty=null;
       item.mixedParts=item.parts.slice();
     }
   }

   if(!item.offerItem && state.offerStatus==="live"){
     item.offers=state.offers.filter(o=>matchOfferToRecipe(o,{name:item.name,ingredients:[item.name]})>0).slice(0,1)
   }
 }

 return [...map.values()]
   .filter(x=>!state.hiddenShop.has(x.key))
   .map(x=>({...x,purchase:purchasePlan(x)}))
   .sort((a,b)=>Number(b.offerItem)-Number(a.offerItem)||a.name.localeCompare(b.name,"sv"))
}
function fmtQty(x){if(x.qty===null)return"";let q=Math.round(x.qty*100)/100;if(x.unit==="g"&&q>=1000)return`${Math.round(q/100)/10} kg`;if(x.unit==="ml"&&q>=1000)return`${Math.round(q/100)/10} l`;return`${String(q).replace(".",",")} ${x.unit}`.trim()}
function offerCost(o){
 let p=canon(o.price);
 let m=p.match(/(\d+)\s*för\s*(\d+(?:[.,]\d+)?)/);
 if(m)return {cost:Number(m[2].replace(",",".")),qty:Number(m[1]),type:"bundle"};
 m=p.match(/(\d+(?:[.,]\d+)?)\s*kr\s*\/\s*st/);
 if(m)return {cost:Number(m[1].replace(",",".")),qty:1,type:"st"};
 m=p.match(/(\d+(?:[.,]\d+)?)\s*:-\s*\/?\s*st/);
 if(m)return {cost:Number(m[1].replace(",",".")),qty:1,type:"st"};
 return null
}
function estimateShop(){
 let items=shopping(),planned=0,priced=0,total=0,missing=[];
 for(const item of items){
   total++;
   if(item.offerItem&&Number(item.plannedCost)>0){planned+=Number(item.plannedCost);priced++;continue}
   let p=realProductForItem(item);
   if(p){planned+=p.cost;priced++}
   else missing.push(item.name)
 }
 return {planned,priced,total,missing}
}

function budgetPeriod(date=new Date()){
 let y=date.getFullYear(),m=date.getMonth();
 let start=date.getDate()>=25?new Date(y,m,25,12):new Date(y,m-1,25,12);
 let end=new Date(start.getFullYear(),start.getMonth()+1,24,23,59,59);
 return {start,end};
}
function budgetPeriodLabel(){
 let p=budgetPeriod();
 return `${shortDate(p.start)}–${shortDate(p.end)}`;
}
function monthSpent(){
 let p=budgetPeriod();
 return state.expenses.filter(x=>{
   let d=new Date(x.date);
   return d>=p.start && d<=p.end
 }).reduce((s,x)=>s+Number(x.amount||0),0)
}

function offerId(o){return canon((o.name||"")+"|"+(o.price||""))}
function offerInCart(o){let id=offerId(o);return state.offerCart.some(x=>x.id===id)}
function addOfferToCart(o){
 let id=offerId(o);
 if(state.offerCart.some(x=>x.id===id))return;
 let parsed=offerCost(o);
 state.offerCart.push({
   id,name:o.name,price:o.price,details:o.details||"",
   dealQty:parsed?.qty||1,plannedCost:parsed?.cost??null
 });
 save();render();
}
function removeOfferFromCart(id){
 state.offerCart=state.offerCart.filter(x=>x.id!==id);
 save();render();
}
function plannedOfferTotal(){return estimateShop().planned}
function offerCoverageText(){
 if(state.offerStatus!=="live")return "";
 let total=Number(state.offerPageCount)||state.offers.length;
 return total>state.offers.length?`${state.offers.length} av ${total} erbjudanden`:`${state.offers.length} erbjudanden`;
}
function featuredOffers(){
 if(state.offerStatus!=="live")return"";
 let useful=state.offers.filter(o=>state.week.some(p=>matchOfferToRecipe(o,p.recipe)>0)).slice(0,6);
 if(!useful.length) useful=state.offers.slice(0,6);
 return `<section class="deal-focus"><div class="deal-focus-head"><div><span class="kicker">ICA Maxi Växjö</span><h2>Veckans fynd</h2></div><button class="deal-link" data-goto="offers">Alla ${state.offers.length} ›</button></div><div class="deal-scroll">${useful.map(o=>`<div class="deal-card"><b>${esc(o.name)}</b><span>${esc(o.price||"Erbjudande")}</span><button data-offer-add="${esc(offerId(o))}" ${offerInCart(o)?"disabled":""}>${offerInCart(o)?"✓ Tillagd":"＋ Lägg till"}</button></div>`).join("")}</div></section>`;
}
function budgetSummary(){
 let spent=monthSpent(),est=estimateShop(),planned=est.planned,left=Math.max(0,state.settings.monthlyBudget-spent),projected=Math.max(0,state.settings.monthlyBudget-spent-planned);
 let pct=Math.min(100,Math.round(spent/state.settings.monthlyBudget*100)||0);
 let weekPct=Math.min(100,Math.round(planned/state.settings.weeklyBudget*100)||0);
 return `<div class="budget-main-row">
   <div><span class="kicker">Veckans inköp</span><strong>${Math.round(planned).toLocaleString("sv-SE")} kr</strong></div>
   <div class="budget-target ${planned>state.settings.weeklyBudget?"over":""}">mål ${state.settings.weeklyBudget.toLocaleString("sv-SE")} kr</div>
 </div>
 <div class="budget-track weekly"><span style="width:${weekPct}%"></span></div>
 <div class="budget-mini-row"><span>${est.priced}/${est.total} priser</span>${est.missing.length?`<span>${est.missing.length} saknas</span>`:`<span>Alla priser klara</span>`}</div>
 <div class="budget-divider"></div>
 <div class="budget-head"><div><span class="kicker">25:e–24:e</span><strong>${Math.round(spent).toLocaleString("sv-SE")} kr registrerat</strong></div><span class="budget-left">${Math.round(left).toLocaleString("sv-SE")} kr kvar</span></div>
 <div class="budget-track"><span style="width:${pct}%"></span></div>
 <div class="budget-foot"><span>Budget ${state.settings.monthlyBudget.toLocaleString("sv-SE")} kr</span><span>Efter veckolistan: ${Math.round(projected).toLocaleString("sv-SE")} kr kvar</span></div>`;
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

const SHOP_CATEGORIES=[
 ["Frukt & grönt",/banan|äpple|päron|apelsin|citron|lime|avokado|tomat|gurka|paprika|morot|potatis|lök|vitlök|purjolök|sallad|spenat|broccoli|blomkål|zucchini|aubergine|svamp|champinjon|majs|frukt|bär|kål|ingefära|persilja|dill|basilika|koriander/],
 ["Kött & fisk",/kyckling|köttfärs|nötfärs|blandfärs|fläsk|bacon|skinka|korv|falukorv|kassler|kött|lax|torsk|fisk|räk|tonfisk|kebab/],
 ["Mejeri & ägg",/mjölk|grädde|crème fraiche|creme fraiche|yoghurt|fil|kvarg|smör|margarin|ost|ägg|färskost|mozzarella|parmesan/],
 ["Bröd",/bröd|fralla|baguette|tortilla|wrap|pitabröd|hamburgerbröd|korvbröd/],
 ["Frys",/fryst|glass|pommes|fryspizza/],
 ["Snacks & dryck",/chips|snacks|godis|choklad|läsk|cola|saft|juice|mineralvatten|kaffe|te\b|nötter|popcorn/],
 ["Skafferi",/pasta|spaghetti|makaron|ris|couscous|bulgur|nudel|mjöl|socker|havregryn|bakpulver|vaniljsocker|krossade tomater|passerade tomater|tomatpuré|kokosmjölk|böna|kikärt|linser|olja|vinäger|soja|senap|ketchup|majonnäs|buljong|fond|salt|peppar|paprikapulver|curry|oregano|timjan|kanel|krydda|sås/]
];

function shopCategory(name){
 let n=canon(name);
 for(const [label,re] of SHOP_CATEGORIES)if(re.test(n))return label;
 return "Övrigt";
}

function shopRow(x){
 let p=realProductForItem(x),plan=x.purchase||purchasePlan(x),direct=x.offerItem&&x.plannedCost;
 return `<div class="check-row ${state.checked.has(x.key)?"done":""}">
   <input type="checkbox" data-check="${esc(x.key)}" ${state.checked.has(x.key)?"checked":""} aria-label="Klar">
   <label><b>${esc(x.name)}</b>${
     direct
       ? `<span class="quantity">${esc(plan.label)}</span><small class="buy-plan">🔥 ${Math.round(x.plannedCost)} kr</small>`
       : p
         ? `<span class="quantity">${p.packs>1?`${p.packs} × `:""}${esc(p.pack||plan.label)}</span><small class="buy-plan">${p.cost.toFixed(2).replace(".",",")} kr${p.promotion?` · 🔥 Erbjudande`:""}</small>`
         : `<span class="quantity">${esc(plan.label)}</span><small class="buy-plan missing-price">Pris saknas</small>`
   }</label>
   <button class="remove-shop" data-remove-shop="${esc(x.key)}" ${x.offerItem?`data-remove-offer="${esc(x.offers[0].id)}"`:""} aria-label="Ta bort">×</button>
 </div>`;
}

function groupedShoppingList(items){
 if(!items.length)return `<div class="empty-state"><b>Listan är tom</b><span>Lägg till en vara ovan.</span></div>`;
 const order=["Frukt & grönt","Kött & fisk","Mejeri & ägg","Bröd","Skafferi","Frys","Snacks & dryck","Övrigt"];
 const groups=new Map(order.map(x=>[x,[]]));
 items.forEach(x=>(groups.get(shopCategory(x.name))||groups.get("Övrigt")).push(x));
 return order.filter(cat=>groups.get(cat).length).map(cat=>`
   <section class="shop-category">
     <div class="shop-category-head"><h2>${esc(cat)}</h2><span>${groups.get(cat).length}</span></div>
     <div class="shopping-list">${groups.get(cat).map(shopRow).join("")}</div>
   </section>
 `).join("");
}

function shopView(){
 let items=shopping(),done=items.filter(x=>state.checked.has(x.key)).length,remaining=Math.max(0,items.length-done),suggestions=quickSuggestions(),est=estimateShop();
 return `<section class="page-head shop-page-head"><span class="kicker">Handla</span><h1>Inköpslista</h1><p>${remaining} kvar${done?` · ${done} klara`:""}</p></section>
 <section class="add-shop-card"><label for="quickAddInput">Lägg till vara</label><div class="quick-add-row"><input id="quickAddInput" autocomplete="off" placeholder="T.ex. mjölk"><button id="quickAddBtn" aria-label="Lägg till">＋</button></div><div class="smart-chips">${suggestions.map(x=>`<button class="smart-chip" data-quick-add="${esc(x)}">${esc(x)}</button>`).join("")}</div></section>
 <div class="budget-card">${budgetSummary()}<div class="budget-actions"><button class="secondary-btn" id="addGroceryExpense">＋ Registrera butik</button><button class="tertiary-btn" id="addTakeaway">🍕 Hämtmat</button></div></div>
 <div class="list-toolbar"><div><b>Att köpa</b>${est.missing.length?`<small>${est.missing.length} ${est.missing.length===1?"vara saknar":"varor saknar"} pris</small>`:""}</div><button class="text-link" data-goto="offers">ICA-erbjudanden</button></div>
 <div class="shopping-groups">${groupedShoppingList(items)}</div>`;
}
function offersView(){
 let offers=state.offers||[],total=Number(state.offerPageCount)||offers.length;
 return `<section class="page-head"><span class="kicker">Maxi ICA Växjö</span><h1>Erbjudanden</h1><p>${offers.length}${total>offers.length?` av ${total}`:""} aktuella</p></section>
 <div class="offer-search-wrap"><input id="offerSearch" class="search" placeholder="Sök erbjudanden"></div>
 <section id="offerList" class="offer-list">${offerRows(offers)}</section>`;
}
function recipeView(){
 let sourced=state.recipes.filter(r=>approvedSourceRecipe(r)).length;
 return `<section class="page-head"><span class="kicker">Receptbank</span><h1>Hitta något gott</h1><p>${sourced} från ICA, Arla och Köket${state.customRecipes.length?` · ${state.customRecipes.length} egna`:""}</p></section>
 <div class="recipe-actions"><input class="search" id="search" placeholder="Sök recept eller ingrediens, t.ex. köttfärs…"><button class="add-recipe-btn" id="addRecipe">＋ Eget</button></div><div id="recipeResultCount" class="recipe-result-count">${state.recipes.length} recept</div>
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
 document.querySelectorAll("[data-remove-shop]").forEach(b=>b.onclick=()=>{
   if(b.dataset.removeOffer)removeOfferFromCart(b.dataset.removeOffer);
   else{state.hiddenShop.add(b.dataset.removeShop);save();render()}
 });
 document.querySelectorAll("[data-quick-add]").forEach(b=>b.onclick=()=>addQuickItem(b.dataset.quickAdd));
 document.querySelectorAll("[data-offer-add]").forEach(b=>b.onclick=()=>{let o=state.offers.find(x=>offerId(x)===b.dataset.offerAdd);if(o)addOfferToCart(o)});
 if($("#offerSearch"))$("#offerSearch").oninput=e=>{state.offerSearch=e.currentTarget.value;$("#view").innerHTML=offersView();wire()};
 if($("#quickAddBtn"))$("#quickAddBtn").onclick=()=>addQuickItem($("#quickAddInput").value);
 if($("#quickAddInput"))$("#quickAddInput").onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();addQuickItem(e.currentTarget.value)}};
 if($("#addRecipe"))$("#addRecipe").onclick=addOwnRecipe;
 if($("#search"))$("#search").oninput=filterRecipes;
 if($("#addGroceryExpense"))$("#addGroceryExpense").onclick=()=>addExpense("Matbutik");
 if($("#addTakeaway"))$("#addTakeaway").onclick=()=>addExpense("Hämtmat");
 document.querySelectorAll("[data-filter]").forEach(b=>b.onclick=()=>{document.querySelectorAll("[data-filter]").forEach(x=>x.classList.remove("active"));b.classList.add("active");state.filter=b.dataset.filter;filterRecipes()});
}
function swapMeal(i){let cur=state.week[i].recipe,counts={};state.week.forEach((p,j)=>{if(j!==i)counts[mainGroup(p.recipe)]=(counts[mainGroup(p.recipe)]||0)+1});let all=state.recipes.filter(r=>recipeKey(r)!==recipeKey(cur)&&!state.disliked.has(recipeKey(r))&&!state.week.some((p,j)=>j!==i&&recipeKey(p.recipe)===recipeKey(r)));let allowed=all.filter(r=>{let g=mainGroup(r);return g==="annat"||(counts[g]||0)<2});let pool=allowed;pool.sort((a,b)=>baseScore(b,i,counts)-baseScore(a,i,counts));if(pool[0])state.week[i]={...state.week[i],recipe:pool[0]};render()}
function showRecipe(id){let r=state.recipes.find(x=>recipeKey(x)===id);if(!r)return;let key=recipeKey(r),body=`${image(r,"sheet-image")}<div class="source-badge">${esc(r.source||"Matappen")}</div><h3>${esc(r.name)}</h3><div class="row">${meta(r)}</div>${offerBadge(r)}<div class="taste-actions"><button class="${state.liked.has(key)?'taste-on':''}" id="likeRecipe">👍 Den här gillar vi</button><button class="${state.disliked.has(key)?'taste-bad':''}" id="dislikeRecipe">👎 Inte för oss</button></div>`;if((r.ingredients||[]).length)body+=`<h4>Ingredienser</h4>${r.ingredients.map(x=>`<div class="ingredient">${esc(x)}</div>`).join("")}`;if(r.external&&r.url)body+=`<a href="${esc(r.url)}" target="_blank" rel="noopener" class="wide-btn link-btn">Öppna hos ${esc(r.source)} ↗</a>`;else if(r.steps)body+=`<h4>Gör så här</h4>${r.steps.map((s,i)=>`<div class="step"><b>${i+1}.</b> ${esc(s)}</div>`).join("")}`;showSheet(body);setTimeout(()=>{$("#likeRecipe").onclick=()=>{state.liked.add(key);state.disliked.delete(key);saveTaste();buildWeek();closeSheet();render()};$("#dislikeRecipe").onclick=()=>{state.disliked.add(key);state.liked.delete(key);saveTaste();buildWeek();closeSheet();render()}},10)}
function saveTaste(){localStorage.setItem("likedV24",JSON.stringify([...state.liked]));localStorage.setItem("dislikedV24",JSON.stringify([...state.disliked]))}
function searchGroups(q){const alias={"köttfärs":["köttfärs","nötfärs","blandfärs","färs"],"färs":["färs","köttfärs","nötfärs","blandfärs"],"kyckling":["kyckling","kycklingfilé"],"fisk":["fisk","torsk","sej","lax"],"pasta":["pasta","spaghetti","spagetti","lasagne","makaron","penne"],"grädde":["grädde","vispgrädde","matlagningsgrädde"],"vegetariskt":["vegetar","linser","bönor","tofu","halloumi"]};return canon(q).split(" ").filter(Boolean).map(t=>alias[t]||[t])}
function recipeSearchText(r){return canon([r.name,r.source,...(r.ingredients||[]),...(r.tags||[])].join(" "))}
function filterRecipes(){let q=$("#search").value.trim(),f=state.filter,groups=searchGroups(q),arr=state.recipes.filter(r=>{if(!groups.length)return true;let hay=recipeSearchText(r);return groups.every(g=>g.some(t=>hay.includes(canon(t))))});if(f==="≤30 min")arr=arr.filter(r=>mins(r)&&mins(r)<=30);if(["ICA","Arla","Köket"].includes(f))arr=arr.filter(r=>r.source===f);if(f==="👍 Gillade")arr=arr.filter(r=>state.liked.has(recipeKey(r)));if(f==="🔥 ICA-match")arr=arr.filter(r=>offerMatches(r).length);if(q){let cq=canon(q);arr.sort((a,b)=>{let an=canon(a.name),bn=canon(b.name),as=an===cq?4:an.includes(cq)?3:recipeSearchText(a).includes(cq)?2:1,bs=bn===cq?4:bn.includes(cq)?3:recipeSearchText(b).includes(cq)?2:1;return bs-as||a.name.localeCompare(b.name,"sv")})}$("#recipeList").innerHTML=arr.length?recipeCards(arr.slice(0,220)):`<div class="card empty-state"><b>Inga träffar</b><span>Prova ett bredare ord, till exempel färs, pasta eller fisk.</span></div>`;let c=$("#recipeResultCount");if(c)c.textContent=`${arr.length} recept`;document.querySelectorAll(".recipe-card").forEach(c=>c.onclick=()=>showRecipe(c.dataset.id))}

function addOwnRecipe(){showSheet(`<h3>＋ Eget recept</h3><label class="form-label">Namn</label><input class="search" id="ownName"><div class="form-grid"><div><label class="form-label">Portioner</label><input class="search" id="ownPortions" value="4"></div><div><label class="form-label">Tid, min</label><input class="search" id="ownMinutes"></div></div><label class="form-label">Ingredienser – en per rad</label><textarea class="recipe-textarea" id="ownIngredients"></textarea><label class="form-label">Gör så här</label><textarea class="recipe-textarea" id="ownSteps"></textarea><button class="wide-btn" id="saveOwnRecipe">Spara recept</button>`);setTimeout(()=>{$("#saveOwnRecipe").onclick=()=>{let name=$("#ownName").value.trim(),ingredients=$("#ownIngredients").value.split(/\n/).map(x=>x.trim()).filter(Boolean);if(!name||!ingredients.length)return;let r={id:"own-"+Date.now(),name,source:"Eget recept",external:false,ingredients,steps:$("#ownSteps").value.split(/\n/).filter(Boolean),minutes:Number($("#ownMinutes").value)||null,portions:Number($("#ownPortions").value)||4,tags:["eget"]};state.customRecipes.unshift(r);localStorage.setItem("customRecipes",JSON.stringify(state.customRecipes));state.recipes.unshift(r);buildWeek();closeSheet();render()}},10)}
function addExpense(type){showSheet(`<h3>${type==='Hämtmat'?'🍕 Hämtmat':'🛒 Matbutik'}</h3><input class="search" id="expenseAmount" inputmode="decimal" placeholder="Belopp i kr"><button class="wide-btn" id="saveExpense">Spara</button>`);setTimeout(()=>{$("#saveExpense").onclick=()=>{let amount=Number($("#expenseAmount").value.replace(",","."));if(!amount)return;state.expenses.push({date:new Date().toISOString().slice(0,10),type,amount});save();closeSheet();render()}},10)}
function customAdd(){
 showSheet(`<h3>Lägg till vara</h3><input class="search" id="customInput" placeholder="Vad behöver ni?"><button class="wide-btn" id="saveCustom">Lägg till</button>`);
 setTimeout(()=>{$("#saveCustom").onclick=()=>{addQuickItem($("#customInput").value);closeSheet()}},10)
}
function showInfo(){
 ensureAnchor();
 showSheet(`<div class="sheet-kicker">Inställningar</div><h3>Matappen v45</h3><p class="sheet-intro">Matveckan går torsdag–onsdag och budgeten den 25:e–24:e.</p>
 <label class="form-label">Ankare för barnveckan</label><input class="search" type="date" id="anchorThursday" value="${esc(state.settings.anchorThursday)}">
 <label class="form-label">Den torsdagen</label><select class="search" id="handover"><option value="arrival" ${state.settings.handover==="arrival"?"selected":""}>kommer barnen</option><option value="departure" ${state.settings.handover==="departure"?"selected":""}>lämnas barnen</option></select>
 <div class="settings-note">Välj en torsdag du vet stämmer. Därefter växlar Matappen automatiskt varannan torsdag.</div>
 <div class="form-grid"><div><label class="form-label">Veckomål</label><input class="search" id="weeklyBudget" inputmode="numeric" value="${state.settings.weeklyBudget}"></div><div><label class="form-label">Månadsbudget</label><input class="search" id="monthlyBudget" inputmode="numeric" value="${state.settings.monthlyBudget}"></div></div>
 <div class="settings-note">Budgetperioden är alltid den 25:e till den 24:e. Den nya potten börjar automatiskt den 25:e.</div>
 <button class="wide-btn" id="saveSettings">Spara inställningar</button>
 <div class="settings-note">${offerCoverageText()}</div>`);
 setTimeout(()=>{$("#saveSettings").onclick=()=>{
   let anchor=$("#anchorThursday").value;
   if(anchor){
     let a=parseLocalDate(anchor),diff=(a.getDay()-4+7)%7;
     if(diff!==0){a.setDate(a.getDate()-diff);anchor=localDateKey(a)}
     state.settings.anchorThursday=anchor;
   }
   state.settings.handover=$("#handover").value;
   state.settings.weeklyBudget=Number($("#weeklyBudget").value)||1600;
   state.settings.monthlyBudget=Number($("#monthlyBudget").value)||12000;
   save();buildWeek();closeSheet();render()
 }},10)
}
function showSheet(html){$("#sheet").innerHTML=html;$("#sheetBackdrop").classList.remove("hidden");$("#sheet").classList.remove("hidden");$("#sheetBackdrop").onclick=closeSheet}function closeSheet(){$("#sheetBackdrop").classList.add("hidden");$("#sheet").classList.add("hidden")}
init();

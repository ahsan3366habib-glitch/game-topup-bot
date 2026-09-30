
const PACKAGES={
diamonds:[
["25 Diamonds",23],["50 Diamonds",40],["115 Diamonds",82],["240 Diamonds",158],["610 Diamonds",392],["1240 Diamonds",780],["2530 Diamonds",1560]
],
membership:[["Weekly Membership",159],["Weekly Lite",45]],
monthly:[["Monthly Membership",775]],
levelup:[["Level Up-6",50],["Level Up-10",80],["Level Up-15",80],["Level Up-20",80],["Level Up-25",80],["Level Up-30",130]]
};
const paymentNumbers={bKash:"01316897399",Nagad:"01410897399",Upay:"01316897399"};
let selectedPackage=null, selectedPrice=null;
const API={me:"/api/me",login:"/api/login",register:"/api/register",logout:"/api/logout",orders:"/api/orders",myOrders:"/api/my-orders"};

function go(page){
 document.querySelectorAll(".page").forEach(x=>x.classList.remove("active-page"));
 document.getElementById(page)?.classList.add("active-page");
 document.querySelectorAll(".nav-item,.mnav").forEach(x=>x.classList.toggle("active",x.dataset.page===page));
 window.scrollTo({top:0,behavior:"smooth"});
 if(page==="orders") loadOrders();
}
document.querySelectorAll("[data-page]").forEach(b=>b.addEventListener("click",()=>go(b.dataset.page)));

function renderPackages(cat="diamonds",target="packages"){
 const el=document.getElementById(target); if(!el)return;
 el.innerHTML=(PACKAGES[cat]||[]).map(([name,price],i)=>`
 <article class="package">
   ${cat==="diamonds"?'<span class="diamond">💎</span>':'<span class="diamond">'+(cat==="levelup"?'🚀':'👑')+'</span>'}
   ${i===2&&cat==="diamonds"?'<small style="position:absolute;top:7px;right:7px;color:#fff;background:#a82cff;padding:3px 7px;border-radius:8px">Popular</small>':''}
   <div class="name">${name}</div><div class="price">৳ ${price}</div>
   <button onclick="openOrder('${name.replace(/'/g,"\\'")}',${price})">Order Now →</button>
 </article>`).join("");
}
document.querySelectorAll(".tab").forEach(t=>t.addEventListener("click",()=>{
 document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));t.classList.add("active");
 renderPackages(t.dataset.cat,"packages");
}));
renderPackages("diamonds","packages"); renderPackages("diamonds","topupPackages");

function selectGame(game){document.querySelectorAll(".game-card").forEach(x=>x.classList.remove("active"));event.currentTarget.classList.add("active");if(game==="Free Fire")go("topup");}
function openOrder(name,price){selectedPackage=name;selectedPrice=price;document.getElementById("orderModal").classList.add("show");}
function closeModal(){document.getElementById("orderModal").classList.remove("show")}
function copyPayment(){navigator.clipboard?.writeText(document.getElementById("paymentNumber").textContent);alert("Payment number copied");}
document.getElementById("paymentMethod").addEventListener("change",e=>document.getElementById("paymentNumber").textContent=paymentNumbers[e.target.value]);

async function submitOrder(){
 const uid=document.getElementById("playerUid").value.trim(),trx=document.getElementById("transactionId").value.trim(),method=document.getElementById("paymentMethod").value;
 if(!uid||!trx){alert("UID এবং Transaction ID দিন");return}
 try{
  const r=await fetch(API.orders,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({package:selectedPackage,price:selectedPrice,uid,payment_method:method,trx_id:trx})});
  const d=await r.json(); if(!r.ok)throw new Error(d.error||"Order failed");
  alert("Order submitted successfully");closeModal();loadOrders();
 }catch(e){alert("Order submit করতে সমস্যা: "+e.message)}
}
async function loadOrders(){
 const box=document.getElementById("myOrders"); if(!box)return;
 try{const r=await fetch(API.myOrders);const d=await r.json();if(!d.orders?.length){box.textContent="এখনও কোনো order নেই।";return}
 box.innerHTML=d.orders.map(o=>`<div class="live-row"><div class="live-avatar">💎</div><div><b>${o.package||"Topup"}</b><small style="display:block;color:#8390b6">৳${o.price} • ${o.uid||""}</small></div><span class="status">${o.status||"Pending"}</span></div>`).join("")
 }catch{box.textContent="Login করলে order status দেখা যাবে।"}
}
const liveData=[
["Rafid_07","Free Fire 310 Diamonds","Completed"],["Xgaming_BD","PUBG UC 325+","Completed"],["Sakib_05","eFootball 540 Coins","Processing"],["Tawhid_11","Call of Duty CP 1080","Completed"]
];
function renderLive(id){
 const el=document.getElementById(id);if(!el)return;
 el.innerHTML=liveData.map((x,i)=>`<div class="live-row"><div class="live-avatar">${["🔥","🎮","⚽","🎯"][i]}</div><div><b>${x[0]}</b><small style="display:block;color:#8390b6">${x[1]}<br>${i+2} mins ago</small></div><span class="status ${x[2]==="Processing"?"processing":""}">${x[2]}</span></div>`).join("")
}
renderLive("liveOrders");renderLive("livePageOrders");

async function updateMe(){
 try{const r=await fetch(API.me);const d=await r.json();if(d.logged_in){document.getElementById("accountText").textContent=d.user?.name||"Account"}}catch{}
}
document.getElementById("loginBtn").onclick=()=>alert("Login/Signup form আপনার existing backend-এর সাথে connect করতে পারবে।");
document.getElementById("settingsLogin").onclick=()=>document.getElementById("loginBtn").click();
document.getElementById("logoutBtn").onclick=async()=>{try{await fetch(API.logout,{method:"POST"});location.reload()}catch{}};
updateMe();

document.getElementById("searchInput").addEventListener("input",e=>{
 const q=e.target.value.toLowerCase();
 document.querySelectorAll(".game-card,.package").forEach(el=>el.style.display=el.textContent.toLowerCase().includes(q)?"":"none");
});

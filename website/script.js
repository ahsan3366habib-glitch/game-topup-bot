const API={me:"/api/me",login:"/api/login",register:"/api/register",logout:"/api/logout",orders:"/api/orders",myOrders:"/api/my-orders",packages:"/api/packages"};
let packages=[
 {key:"d25",name:"25 Diamonds",price:23,cat:"diamonds"},{key:"d50",name:"50 Diamonds",price:40,cat:"diamonds"},
 {key:"d115",name:"115 Diamonds",price:82,cat:"diamonds"},{key:"d240",name:"240 Diamonds",price:158,cat:"diamonds"},
 {key:"d610",name:"610 Diamonds",price:392,cat:"diamonds"},{key:"d1240",name:"1240 Diamonds",price:780,cat:"diamonds"},
 {key:"d2530",name:"2530 Diamonds",price:1560,cat:"diamonds"},{key:"weekly",name:"Weekly Membership",price:159,cat:"membership"},
 {key:"wlite",name:"Weekly Lite",price:45,cat:"membership"},{key:"monthly",name:"Monthly Membership",price:775,cat:"monthly"},
 {key:"lu6",name:"Level Up-6",price:50,cat:"levelup"},{key:"lu10",name:"Level Up-10",price:80,cat:"levelup"},
 {key:"lu15",name:"Level Up-15",price:80,cat:"levelup"},{key:"lu20",name:"Level Up-20",price:80,cat:"levelup"},
 {key:"lu25",name:"Level Up-25",price:80,cat:"levelup"},{key:"lu30",name:"Level Up-30",price:130,cat:"levelup"}
];
let currentUser=null,selectedPackage=null,currentCat="diamonds";
const $=id=>document.getElementById(id);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
function toast(t){const e=$("toast");e.textContent=t;e.classList.add("show");setTimeout(()=>e.classList.remove("show"),2500)}
function openModal(id){$(id).classList.add("show")} function closeModal(id){$(id).classList.remove("show")}
function openPage(p){
 document.querySelectorAll(".page").forEach(x=>x.classList.remove("active"));
 $(p+"Page").classList.add("active");
 document.querySelectorAll("[data-page]").forEach(x=>x.classList.toggle("active",x.dataset.page===p));
 if(p==="orders")loadOrders(); if(p==="live")renderLiveFull(); if(p==="settings")renderSettings();
 window.scrollTo({top:0,behavior:"smooth"});
}
function showCategory(cat){currentCat=cat;openPage("topup");renderAllPackages();$("categoryTitle").textContent={diamonds:"💎 Diamond Topup",membership:"🎁 Membership",monthly:"🎁 Monthly Membership",levelup:"🎫 Level Up Pass"}[cat]}
function packageCard(p,i=0){
 const icon=p.cat==="diamonds"?"💎":p.cat==="levelup"?"🎫":"🎁";
 return `<article class="package"><span class="diamond">${icon}</span>${i===2?'<span class="popular">Most Popular</span>':''}<h3>${esc(p.name)}</h3><div class="price">৳ ${p.price}</div><button class="glow-btn" onclick="startOrder('${p.key}')">Order Now →</button></article>`
}
function renderHomePackages(){
 const list=packages.filter(p=>p.cat===currentCat).slice(0,5);
 $("homePackages").innerHTML=list.map((p,i)=>packageCard(p,i)).join("");
}
function renderAllPackages(){
 const list=packages.filter(p=>p.cat===currentCat);
 $("allPackages").innerHTML=list.map((p,i)=>packageCard(p,i)).join("")||'<div class="empty">No package found.</div>';
}
function startOrder(key){
 if(!currentUser){openModal("authModal");toast("আগে Login করুন");return}
 selectedPackage=packages.find(p=>p.key===key); if(!selectedPackage)return;
 $("selectedPackage").textContent=selectedPackage.name;$("selectedPrice").textContent=selectedPackage.price;
 $("orderMsg").textContent="";$("orderForm").reset();openModal("orderModal");
}
const liveData=[
 ["Rafid_07","Free Fire 310 Diamonds","Completed","2 mins ago","🧑🏻"],
 ["Xgaming_BD","PUBG UC 325+","Completed","5 mins ago","🎮"],
 ["Sakib_05","eFootball 540 Coins","Processing","8 mins ago","🧑🏽"],
 ["Tawhid_11","Call of Duty CP 1080","Completed","12 mins ago","🧑🏾"]
];
function liveItem(x){
 const processing=x[2]==="Processing";
 return `<div class="live-item"><span class="live-avatar">${x[4]}</span><div><b>${x[0]}</b><small>${x[1]}</small></div><div><span class="live-status ${processing?"processing":""}">${x[2]}</span><small>${x[3]}</small></div></div>`
}
function renderLive(){ $("liveOrdersSide").innerHTML=liveData.map(liveItem).join("");$("liveBadge").textContent=liveData.length}
function renderLiveFull(){ $("liveOrdersFull").innerHTML=liveData.map(liveItem).join("")}
function renderSettings(){
 $("settingsUser").textContent=currentUser?`${currentUser.name} • ${currentUser.email}`:"Guest — Login করে order করতে পারবেন";
 $("settingsAuth").classList.toggle("hidden",!!currentUser);$("logoutBtn").classList.toggle("hidden",!currentUser);
}
async function loadPackages(){
 try{const r=await fetch(API.packages);if(r.ok){const d=await r.json();if(Array.isArray(d)&&d.length)packages=packages.map((old)=>{const x=d.find(y=>String(y.key)===old.key||String(y.name)===old.name);return x?{...old,...x}:old})}}catch(e){}
 renderHomePackages();renderAllPackages();
}
async function checkMe(){
 try{const r=await fetch(API.me);const d=await r.json();currentUser=d.authenticated?d.user:null;if(currentUser){$("userName").textContent=currentUser.name;$("userType").textContent="Premium User"}renderSettings()}catch(e){renderSettings()}
}
$("loginTab").onclick=()=>{ $("loginTab").classList.add("active");$("registerTab").classList.remove("active");$("loginForm").classList.remove("hidden");$("registerForm").classList.add("hidden")};
$("registerTab").onclick=()=>{ $("registerTab").classList.add("active");$("loginTab").classList.remove("active");$("registerForm").classList.remove("hidden");$("loginForm").classList.add("hidden")};
$("authBtn").onclick=()=>currentUser?openPage("settings"):openModal("authModal");
$("settingsAuth").onclick=()=>openModal("authModal");
$("logoutBtn").onclick=async()=>{await fetch(API.logout,{method:"POST"});currentUser=null;$("userName").textContent="Guest";$("userType").textContent="";renderSettings();toast("Logged out")};
$("loginForm").onsubmit=async e=>{e.preventDefault();$("authMsg").textContent="Logging in...";const r=await fetch(API.login,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:$("loginEmail").value,password:$("loginPassword").value})});const d=await r.json();if(!r.ok){$("authMsg").textContent=d.error||"Login failed";return}currentUser=d.user;$("userName").textContent=currentUser.name;$("userType").textContent="Premium User";closeModal("authModal");renderSettings();toast("Login successful")};
$("registerForm").onsubmit=async e=>{e.preventDefault();$("authMsg").textContent="Creating account...";const r=await fetch(API.register,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:$("registerName").value,email:$("registerEmail").value,password:$("registerPassword").value})});const d=await r.json();if(!r.ok){$("authMsg").textContent=d.error||"Signup failed";return}currentUser=d.user;$("userName").textContent=currentUser.name;$("userType").textContent="Premium User";closeModal("authModal");renderSettings();toast("Account created")};
$("orderForm").onsubmit=async e=>{e.preventDefault();if(!selectedPackage)return;$("orderMsg").textContent="Submitting...";const payload={player_id:$("playerUid").value.trim(),package_name:selectedPackage.name,payment_method:$("paymentMethod").value,transaction_id:$("transactionId").value.trim()};const r=await fetch(API.orders,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});const d=await r.json();if(!r.ok){$("orderMsg").textContent=d.error||"Order failed";return}closeModal("orderModal");toast(`Order #${d.order_id} submitted`);openPage("orders")};
async function loadOrders(){
 if(!currentUser){$("myOrdersList").innerHTML='<div class="empty">Login করলে তোমার order দেখা যাবে।</div>';return}
 $("myOrdersList").innerHTML='<div class="empty">Loading...</div>';
 try{const r=await fetch(API.myOrders);const d=await r.json();if(!Array.isArray(d)||!d.length){$("myOrdersList").innerHTML='<div class="empty">এখনও কোনো order নেই।</div>';return}
 $("myOrdersList").innerHTML=d.map(o=>`<div class="order-row"><div><b>#${o.id} • ${esc(o.package_name)}</b><span>UID: ${esc(o.player_id)} • ৳${o.amount} • ${esc(o.payment_method)}</span><small>${esc(o.created_at)}</small></div><span class="status ${o.status}">${o.status==="completed"?"Completed":o.status==="payment_verified"?"Payment Verified":o.status==="rejected"?"Rejected":"Payment Pending"}</span></div>`).join("")
 }catch(e){$("myOrdersList").innerHTML='<div class="empty">Order load করা যায়নি।</div>'}
}
$("paymentMethod").onchange=()=>{const n={bKash:"01316897399",Nagad:"01410897399",Upay:"01316897399"}[$("paymentMethod").value];$("paymentInfo").innerHTML=n?`Payment করতে <b>Send Money</b> করুন: <strong>${n}</strong>`:"Payment করতে <b>Send Money</b> করুন।"};
document.querySelectorAll("[data-page]").forEach(x=>x.onclick=()=>openPage(x.dataset.page));
document.querySelectorAll(".category-tabs button").forEach(x=>x.onclick=()=>{document.querySelectorAll(".category-tabs button").forEach(b=>b.classList.remove("active"));x.classList.add("active");currentCat=x.dataset.cat;renderHomePackages()});
$("searchInput").oninput=e=>{const q=e.target.value.toLowerCase();$("homePackages").innerHTML=packages.filter(p=>p.name.toLowerCase().includes(q)).map((p,i)=>packageCard(p,i)).join("")||'<div class="empty">No package found.</div>'};
window.onclick=e=>{if(e.target.classList.contains("modal"))e.target.classList.remove("show")};
renderLive();renderLiveFull();renderHomePackages();renderAllPackages();checkMe();loadPackages();

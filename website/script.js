const API={me:"/api/me",login:"/api/login",register:"/api/register",logout:"/api/logout",orders:"/api/orders",myOrders:"/api/my-orders",packages:"/api/packages"};

let packages=[];
let currentUser=null;
let selectedPackage=null;

const $=id=>document.getElementById(id);

function toast(msg){
  const el=$("toast"); el.textContent=msg; el.classList.add("show");
  setTimeout(()=>el.classList.remove("show"),2600);
}
function openModal(id){$(id).classList.add("show")}
function closeModal(id){$(id).classList.remove("show")}
function openPage(page){
  document.querySelectorAll(".page").forEach(x=>x.classList.remove("active"));
  const target=$(page+"Page"); if(target) target.classList.add("active");
  document.querySelectorAll("[data-page]").forEach(x=>x.classList.toggle("active",x.dataset.page===page));
  if(page==="orders") loadOrders();
  if(page==="settings") renderSettings();
  window.scrollTo({top:0,behavior:"smooth"});
}
function selectGame(){openPage("topup")}
function authOpen(){openModal("authModal")}
function setAuthTab(mode){
  $("loginTab").classList.toggle("active",mode==="login");
  $("registerTab").classList.toggle("active",mode==="register");
  $("loginForm").classList.toggle("hidden",mode!=="login");
  $("registerForm").classList.toggle("hidden",mode!=="register");
  $("authMsg").textContent="";
}
function requireLogin(){
  if(!currentUser){authOpen();return false}
  return true;
}
function renderAuth(){
  $("userBadge").textContent=currentUser?currentUser.name:"Guest";
  $("authBtn").textContent=currentUser?"Account":"Login";
  $("logoutBtn").classList.toggle("hidden",!currentUser);
}
function renderSettings(){
  $("settingsUser").textContent=currentUser
    ? `Logged in as ${currentUser.name} (${currentUser.email})`
    : "You are browsing as Guest.";
  $("settingsAuth").classList.toggle("hidden",!!currentUser);
}
function packageCard(p){
  return `<div class="package">
    <div class="type">FREE FIRE • MANUAL TOP UP</div>
    <h3>${escapeHtml(p.name)}</h3>
    <div class="price">৳${p.price}</div>
    <button class="btn primary" onclick="startOrder('${escapeAttr(p.key)}')">BUY NOW</button>
  </div>`;
}
function renderPackages(){
  $("allPackages").innerHTML=packages.map(packageCard).join("");
  $("featuredPackages").innerHTML=packages.slice(0,8).map(packageCard).join("");
}
function startOrder(key){
  if(!requireLogin()) return;
  selectedPackage=packages.find(p=>p.key===key);
  if(!selectedPackage)return;
  $("selectedPackage").textContent=selectedPackage.name;
  $("selectedPrice").textContent=selectedPackage.price;
  $("orderForm").reset();
  $("orderMsg").textContent="";
  $("paymentInstruction").innerHTML='Payment করতে <b>Send Money</b> করুন।';
  openModal("orderModal");
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}
function escapeAttr(s){return String(s).replace(/'/g,"\\'")}
function statusLabel(s){
  return {payment_pending:"⏳ Payment Pending",payment_verified:"✅ Payment Verified — Top-up Pending",completed:"🎉 Completed",rejected:"❌ Rejected"}[s]||s;
}
async function loadPackages(){
  try{
    const r=await fetch(API.packages); packages=await r.json(); renderPackages();
  }catch(e){
    packages=[
      {key:"d25",name:"💎 25 Diamonds",price:23},{key:"d50",name:"💎 50 Diamonds",price:40},
      {key:"d115",name:"💎 115 Diamonds",price:82},{key:"d240",name:"💎 240 Diamonds",price:158},
      {key:"d610",name:"💎 610 Diamonds",price:392},{key:"d1240",name:"💎 1240 Diamonds",price:780},
      {key:"d2530",name:"💎 2530 Diamonds",price:1560},{key:"weekly",name:"🎁 Weekly Membership",price:159},
      {key:"wlite",name:"🎁 Weekly Lite",price:45},{key:"monthly",name:"🎁 Monthly Membership",price:775},
      {key:"lu6",name:"🎫 Level Up-6",price:50},{key:"lu10",name:"🎫 Level Up-10",price:80},
      {key:"lu15",name:"🎫 Level Up-15",price:80},{key:"lu20",name:"🎫 Level Up-20",price:80},
      {key:"lu25",name:"🎫 Level Up-25",price:80},{key:"lu30",name:"🎫 Level Up-30",price:130}
    ]; renderPackages();
  }
}
async function checkMe(){
  try{
    const r=await fetch(API.me); const d=await r.json();
    currentUser=d.authenticated?d.user:null; renderAuth(); renderSettings();
  }catch(e){}
}
$("loginForm").addEventListener("submit",async e=>{
  e.preventDefault(); $("authMsg").textContent="Logging in...";
  const r=await fetch(API.login,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:$("loginEmail").value,password:$("loginPassword").value})});
  const d=await r.json();
  if(!r.ok){$("authMsg").textContent=d.error||"Login failed";return}
  currentUser=d.user; closeModal("authModal"); renderAuth(); renderSettings(); toast("Login successful"); loadOrders();
});
$("registerForm").addEventListener("submit",async e=>{
  e.preventDefault(); $("authMsg").textContent="Creating account...";
  const r=await fetch(API.register,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:$("registerName").value,email:$("registerEmail").value,password:$("registerPassword").value})});
  const d=await r.json();
  if(!r.ok){$("authMsg").textContent=d.error||"Signup failed";return}
  currentUser=d.user; closeModal("authModal"); renderAuth(); renderSettings(); toast("Account created");
});
$("logoutBtn").addEventListener("click",async()=>{
  await fetch(API.logout,{method:"POST"}); currentUser=null; renderAuth(); renderSettings(); loadOrders(); toast("Logged out");
});
$("authBtn").addEventListener("click",()=>currentUser?openPage("settings"):authOpen());
$("settingsAuth").addEventListener("click",authOpen);
$("loginTab").addEventListener("click",()=>setAuthTab("login"));
$("registerTab").addEventListener("click",()=>setAuthTab("register"));
$("paymentMethod").addEventListener("change",()=>{
  const n={bKash:"01316897399",Nagad:"01410897399",Upay:"01316897399"}[$("paymentMethod").value];
  $("paymentInstruction").innerHTML=n?`Payment করতে <b>Send Money</b> করুন: <strong>${n}</strong>`:'Payment করতে <b>Send Money</b> করুন।';
});
$("orderForm").addEventListener("submit",async e=>{
  e.preventDefault(); if(!selectedPackage)return;
  $("orderMsg").textContent="Submitting order...";
  const payload={player_id:$("playerUid").value.trim(),package_name:selectedPackage.name,payment_method:$("paymentMethod").value,transaction_id:$("transactionId").value.trim()};
  const r=await fetch(API.orders,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  const d=await r.json();
  if(!r.ok){$("orderMsg").textContent=d.error||"Order failed";return}
  closeModal("orderModal"); toast(`Order #${d.order_id} submitted`); openPage("orders");
});
async function loadOrders(){
  const box=$("myOrdersList");
  if(!currentUser){box.innerHTML='<div class="empty">Login to view your orders.</div>';return}
  box.innerHTML='<div class="empty">Loading orders...</div>';
  try{
    const r=await fetch(API.myOrders); const d=await r.json();
    if(!r.ok){box.innerHTML=`<div class="empty">${escapeHtml(d.error||"Unable to load orders")}</div>`;return}
    if(!d.length){box.innerHTML='<div class="empty">No orders yet.</div>';return}
    box.innerHTML=d.map(o=>`<div class="order-row"><div><b>#${o.id} • ${escapeHtml(o.package_name)}</b><span>UID: ${escapeHtml(o.player_id)} • ৳${o.amount} • ${escapeHtml(o.payment_method)}</span><small>${escapeHtml(o.created_at)}</small></div><span class="status ${o.status}">${statusLabel(o.status)}</span></div>`).join("");
  }catch(e){box.innerHTML='<div class="empty">Unable to load orders.</div>'}
}
document.querySelectorAll("[data-page]").forEach(btn=>btn.addEventListener("click",()=>openPage(btn.dataset.page)));
$("searchInput").addEventListener("input",e=>{
  const q=e.target.value.toLowerCase().trim();
  const filtered=packages.filter(p=>p.name.toLowerCase().includes(q)||p.key.includes(q));
  $("allPackages").innerHTML=filtered.map(packageCard).join("")||'<div class="empty">No package found.</div>';
});
window.addEventListener("click",e=>{if(e.target.classList.contains("modal"))e.target.classList.remove("show")});
setAuthTab("login"); loadPackages(); checkMe();

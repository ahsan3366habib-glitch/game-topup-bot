const PACKAGES=[
 {k:"lu6",cat:"level",name:"Level Up-6",price:50},
 {k:"lu10",cat:"level",name:"Level Up-10",price:80},
 {k:"lu15",cat:"level",name:"Level Up-15",price:80},
 {k:"lu20",cat:"level",name:"Level Up-20",price:80},
 {k:"lu25",cat:"level",name:"Level Up-25",price:80},
 {k:"lu30",cat:"level",name:"Level Up-30",price:130},
 {k:"wlite",cat:"member",name:"Weekly Lite",price:50},
 {k:"weekly",cat:"member",name:"Weekly Membership",price:170},
 {k:"monthly",cat:"member",name:"Monthly Membership",price:800},
 {k:"d25",cat:"diamond",name:"25 Diamonds",price:25},
 {k:"d50",cat:"diamond",name:"50 Diamonds",price:40},
 {k:"d115",cat:"diamond",name:"115 Diamonds",price:85},
 {k:"d240",cat:"diamond",name:"240 Diamonds",price:165},
 {k:"d610",cat:"diamond",name:"610 Diamonds",price:410},
 {k:"d1240",cat:"diamond",name:"1240 Diamonds",price:800},
 {k:"d2530",cat:"diamond",name:"2530 Diamonds",price:1600}
];

function renderPackages(cat="all"){
 const grid=document.getElementById("packageGrid");
 const select=document.getElementById("package");
 grid.innerHTML="";
 select.innerHTML='<option value="">Select a package</option>';
 PACKAGES.filter(p=>cat==="all"||p.cat===cat).forEach(p=>{
   grid.innerHTML+=`<button class="package-card" type="button" onclick="choosePackage('${p.k}')"><small>${p.cat==="level"?"🎫 Level Up Pass":p.cat==="member"?"🎁 Membership":"💎 Diamonds"}</small><b>${p.name}</b><div class="price">৳${p.price}</div></button>`;
 });
 PACKAGES.forEach(p=>select.innerHTML+=`<option value="${p.k}">${p.name} — ৳${p.price}</option>`);
}
function filterPackages(cat){
 document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("active",t.dataset.cat===cat));
 renderPackages(cat);
}
function choosePackage(k){
 document.getElementById("package").value=k;
 document.getElementById("order").scrollIntoView({behavior:"smooth"});
}
function getOrders(){return JSON.parse(localStorage.getItem("tz_orders")||"[]")}
function saveOrders(o){localStorage.setItem("tz_orders",JSON.stringify(o))}
function renderOrders(){
 const el=document.getElementById("orderList"); if(!el)return;
 const orders=getOrders();
 el.innerHTML=orders.length?orders.slice().reverse().map(o=>`<div class="order-row"><b>#${o.id}</b> · ${o.package}<br>UID: ${o.uid} · ৳${o.amount}<br><span class="status">${o.status}</span></div>`).join(""):"";
}
document.getElementById("orderForm").addEventListener("submit",e=>{
 e.preventDefault();
 const uid=document.getElementById("uid").value.trim();
 const key=document.getElementById("package").value;
 const p=PACKAGES.find(x=>x.k===key);
 const payment=document.getElementById("payment").value;
 const txn=document.getElementById("txn").value.trim();
 if(!/^\d{5,15}$/.test(uid)){alert("সঠিক Free Fire UID দিন।");return}
 if(!p||!payment||txn.length<4){alert("সব তথ্য পূরণ করুন।");return}
 const order={id:"TZ"+Date.now().toString().slice(-7),uid,package:p.name,amount:p.price,payment,txn,status:"Payment Pending",created:new Date().toLocaleString("bn-BD")};
 const orders=getOrders();orders.push(order);saveOrders(orders);renderOrders();
 alert(`✅ Order submitted!\nOrder ID: ${order.id}\nAdmin payment verify করে manual top-up করবেন।`);
 e.target.reset();
});
renderPackages();renderOrders();
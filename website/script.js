/* =========================================================
   CHATNI TOP UP
   PREMIUM GAMING DASHBOARD JS
========================================================= */

const API = {
    me: "/api/me",
    login: "/api/login",
    register: "/api/register",
    logout: "/api/logout",
    orders: "/api/orders",
    myOrders: "/api/my-orders"
};


/* =========================================================
   PACKAGE DATA
========================================================= */

const packages = {

    diamonds: [
        { name: "25 Diamonds", amount: "25 💎", price: 23 },
        { name: "50 Diamonds", amount: "50 💎", price: 40 },
        { name: "115 Diamonds", amount: "115 💎", price: 82 },
        { name: "240 Diamonds", amount: "240 💎", price: 158 },
        { name: "610 Diamonds", amount: "610 💎", price: 392 },
        { name: "1240 Diamonds", amount: "1240 💎", price: 780 },
        { name: "2530 Diamonds", amount: "2530 💎", price: 1560 }
    ],

    membership: [
        { name: "Weekly", amount: "Weekly Membership", price: 159 },
        { name: "Weekly Lite", amount: "Weekly Lite", price: 45 },
        { name: "Monthly", amount: "Monthly Membership", price: 775 }
    ],

    levelup: [
        { name: "Level Up-6", amount: "Level Up-6", price: 50 },
        { name: "Level Up-10", amount: "Level Up-10", price: 80 },
        { name: "Level Up-15", amount: "Level Up-15", price: 80 },
        { name: "Level Up-20", amount: "Level Up-20", price: 80 },
        { name: "Level Up-25", amount: "Level Up-25", price: 80 },
        { name: "Level Up-30", amount: "Level Up-30", price: 130 }
    ]
};


/* =========================================================
   STATE
========================================================= */

let currentUser = null;
let selectedPackage = null;
let selectedPackageType = null;


/* =========================================================
   HELPERS
========================================================= */

function $(selector){
    return document.querySelector(selector);
}

function $$(selector){
    return [...document.querySelectorAll(selector)];
}

function escapeHTML(value){
    if(value === null || value === undefined) return "";

    return String(value)
        .replace(/&/g,"&amp;")
        .replace(/</g,"&lt;")
        .replace(/>/g,"&gt;")
        .replace(/"/g,"&quot;")
        .replace(/'/g,"&#039;");
}


/* =========================================================
   TOAST
========================================================= */

function toast(message,type="success"){

    let container = $(".toast-container");

    if(!container){
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const item = document.createElement("div");

    item.className = `toast ${type}`;
    item.textContent = message;

    container.appendChild(item);

    setTimeout(()=>{
        item.style.opacity = "0";
        item.style.transform = "translateY(10px)";

        setTimeout(()=>{
            item.remove();
        },250);

    },3000);
}


/* =========================================================
   API
========================================================= */

async function api(url,options={}){

    const config = {
        credentials:"include",
        ...options,
        headers:{
            "Content-Type":"application/json",
            ...(options.headers || {})
        }
    };

    const response = await fetch(url,config);

    let data = {};

    try{
        data = await response.json();
    }catch{
        data = {};
    }

    if(!response.ok){

        throw new Error(
            data.message ||
            data.error ||
            "Something went wrong"
        );
    }

    return data;
}


/* =========================================================
   CURRENT USER
========================================================= */

async function loadCurrentUser(){

    try{

        const data = await api(API.me);

        currentUser =
            data.user ||
            data ||
            null;

        updateUserUI();

    }catch{

        currentUser = null;
        updateUserUI();
    }
}


function updateUserUI(){

    const name =
        currentUser?.name ||
        currentUser?.username ||
        currentUser?.email ||
        "Guest";

    $$(".user-name").forEach(el=>{
        el.textContent = name;
    });

    $$(".user-email").forEach(el=>{
        el.textContent =
            currentUser?.email ||
            "Login required";
    });

    $$(".user-avatar").forEach(el=>{
        el.textContent =
            name.charAt(0).toUpperCase();
    });

    const loginButtons = $$(".login-required");

    loginButtons.forEach(el=>{
        el.style.display =
            currentUser ? "" : "none";
    });
}


/* =========================================================
   LOGIN
========================================================= */

async function loginUser(event){

    event?.preventDefault();

    const email =
        $("#loginEmail")?.value.trim();

    const password =
        $("#loginPassword")?.value;

    if(!email || !password){
        toast("Email এবং password দিন","error");
        return;
    }

    try{

        const data = await api(API.login,{
            method:"POST",
            body:JSON.stringify({
                email,
                password
            })
        });

        currentUser =
            data.user ||
            data;

        closeModal("loginModal");

        updateUserUI();

        toast("Login successful!");

        await loadMyOrders();

    }catch(error){

        toast(error.message,"error");
    }
}


/* =========================================================
   REGISTER
========================================================= */

async function registerUser(event){

    event?.preventDefault();

    const name =
        $("#registerName")?.value.trim();

    const email =
        $("#registerEmail")?.value.trim();

    const password =
        $("#registerPassword")?.value;

    if(!name || !email || !password){

        toast(
            "সব তথ্য পূরণ করুন",
            "error"
        );

        return;
    }

    if(password.length < 6){

        toast(
            "Password কমপক্ষে ৬ অক্ষরের দিন",
            "error"
        );

        return;
    }

    try{

        const data = await api(API.register,{
            method:"POST",
            body:JSON.stringify({
                name,
                email,
                password
            })
        });

        currentUser =
            data.user ||
            data;

        closeModal("registerModal");

        updateUserUI();

        toast("Account created successfully!");

    }catch(error){

        toast(error.message,"error");
    }
}


/* =========================================================
   LOGOUT
========================================================= */

async function logoutUser(){

    try{

        await api(API.logout,{
            method:"POST"
        });

    }catch{}

    currentUser = null;

    updateUserUI();

    closeAllModals();

    toast("Logged out successfully");
}


/* =========================================================
   MODALS
========================================================= */

function openModal(id){

    const modal = document.getElementById(id);

    if(modal){
        modal.classList.add("show");
    }
}

function closeModal(id){

    const modal = document.getElementById(id);

    if(modal){
        modal.classList.remove("show");
    }
}

function closeAllModals(){

    $$(".modal").forEach(modal=>{
        modal.classList.remove("show");
    });
}


$$(".modal").forEach(modal=>{

    modal.addEventListener("click",event=>{

        if(event.target === modal){
            modal.classList.remove("show");
        }

    });

});


document.addEventListener("keydown",event=>{

    if(event.key === "Escape"){
        closeAllModals();
    }

});


/* =========================================================
   LOGIN / REGISTER SWITCH
========================================================= */

function showLogin(){

    closeModal("registerModal");
    openModal("loginModal");
}

function showRegister(){

    closeModal("loginModal");
    openModal("registerModal");
}


/* =========================================================
   SELECT PACKAGE
========================================================= */

function selectPackage(type,index){

    if(!packages[type]){
        return;
    }

    const item = packages[type][index];

    if(!item){
        return;
    }

    selectedPackage = item;
    selectedPackageType = type;

    const packageName =
        $("#orderPackage");

    const packagePrice =
        $("#orderPrice");

    if(packageName){
        packageName.value = item.name;
    }

    if(packagePrice){
        packagePrice.value = `৳${item.price}`;
    }

    const hiddenPackage =
        $("#selectedPackage");

    if(hiddenPackage){
        hiddenPackage.value = item.name;
    }

    const hiddenPrice =
        $("#selectedPrice");

    if(hiddenPrice){
        hiddenPrice.value = item.price;
    }

    openModal("orderModal");
}


/* =========================================================
   PACKAGE BUTTON AUTO BIND
========================================================= */

function bindPackageButtons(){

    $$("[data-package-type]").forEach(button=>{

        button.addEventListener("click",()=>{

            const type =
                button.dataset.packageType;

            const index =
                Number(button.dataset.packageIndex);

            selectPackage(type,index);
        });

    });
}


/* =========================================================
   SUBMIT ORDER
========================================================= */

async function submitOrder(event){

    event?.preventDefault();

    if(!currentUser){

        toast(
            "Order করতে আগে Login করুন",
            "error"
        );

        openModal("loginModal");

        return;
    }

    if(!selectedPackage){

        toast(
            "একটি package select করুন",
            "error"
        );

        return;
    }

    const uid =
        $("#playerUid")?.value.trim();

    const payment =
        $("#paymentMethod")?.value;

    const trx =
        $("#transactionId")?.value.trim();

    if(!uid){

        toast(
            "Free Fire UID দিন",
            "error"
        );

        return;
    }

    if(!payment){

        toast(
            "Payment method select করুন",
            "error"
        );

        return;
    }

    if(!trx){

        toast(
            "Transaction ID দিন",
            "error"
        );

        return;
    }

    const payload = {

        game:"Free Fire",

        uid:uid,

        package:selectedPackage.name,

        price:selectedPackage.price,

        payment_method:payment,

        trx_id:trx

    };

    try{

        const data = await api(API.orders,{

            method:"POST",

            body:JSON.stringify(payload)

        });

        closeModal("orderModal");

        $("#playerUid") &&
            ($("#playerUid").value = "");

        $("#transactionId") &&
            ($("#transactionId").value = "");

        toast(
            data.message ||
            "Order submitted successfully!"
        );

        await loadMyOrders();

    }catch(error){

        toast(error.message,"error");
    }
}


/* =========================================================
   MY ORDERS
========================================================= */

async function loadMyOrders(){

    const container =
        $("#myOrdersList");

    if(!container){
        return;
    }

    if(!currentUser){

        container.innerHTML = `
            <div class="empty">
                Login করে আপনার orders দেখতে পারবেন।
            </div>
        `;

        return;
    }

    container.innerHTML = `
        <div class="empty">
            Loading orders...
        </div>
    `;

    try{

        const data =
            await api(API.myOrders);

        const orders =
            Array.isArray(data)
                ? data
                : (
                    data.orders ||
                    data.data ||
                    []
                );

        if(!orders.length){

            container.innerHTML = `
                <div class="empty">
                    এখনো কোনো order নেই।
                </div>
            `;

            return;
        }

        container.innerHTML =
            orders.map(order=>{

                const status =
                    String(
                        order.status ||
                        "pending"
                    ).toLowerCase();

                const statusClass =
                    status.includes("done")
                        ? "done"
                        : status.includes("verify")
                        ? "verified"
                        : status.includes("reject")
                        ? "rejected"
                        : "pending";

                return `

                    <div class="my-order">

                        <div class="my-order-top">

                            <div>
                                <strong>
                                    ${escapeHTML(
                                        order.package ||
                                        "Free Fire"
                                    )}
                                </strong>

                                <small>
                                    UID:
                                    ${escapeHTML(
                                        order.uid ||
                                        "N/A"
                                    )}
                                </small>

                            </div>

                            <span class="status ${statusClass}">
                                ${escapeHTML(
                                    order.status ||
                                    "Pending"
                                )}
                            </span>

                        </div>

                        <div style="
                            margin-top:8px;
                            display:flex;
                            justify-content:space-between;
                            color:#8d91a8;
                            font-size:10px;
                        ">

                            <span>
                                ৳${escapeHTML(
                                    order.price ||
                                    ""
                                )}
                            </span>

                            <span>
                                ${escapeHTML(
                                    order.created_at ||
                                    ""
                                )}
                            </span>

                        </div>

                    </div>

                `;

            }).join("");

    }catch(error){

        container.innerHTML = `
            <div class="empty">
                Orders load করা যাচ্ছে না।
            </div>
        `;
    }
}


/* =========================================================
   OPEN ORDERS
========================================================= */

function openOrders(){

    openModal("ordersModal");

    loadMyOrders();
}


/* =========================================================
   NAVIGATION
========================================================= */

function setActiveNav(target){

    $$(".nav-item").forEach(item=>{
        item.classList.remove("active");
    });

    $$(".mobile-nav button").forEach(item=>{
        item.classList.remove("active");
    });

    $$(`[data-nav="${target}"]`).forEach(item=>{
        item.classList.add("active");
    });
}


function navigate(section){

    setActiveNav(section);

    if(section === "home"){

        window.scrollTo({
            top:0,
            behavior:"smooth"
        });

        return;
    }

    if(section === "topup"){

        const element =
            $("#topupSection");

        if(element){

            element.scrollIntoView({
                behavior:"smooth",
                block:"start"
            });

        }else{

            window.scrollTo({
                top:450,
                behavior:"smooth"
            });
        }

        return;
    }

    if(section === "trajection"){

        openOrders();

        return;
    }

    if(section === "support"){

        const element =
            $("#supportSection");

        if(element){

            element.scrollIntoView({
                behavior:"smooth",
                block:"center"
            });

        }

        return;
    }

    if(section === "setting"){

        openModal("settingsModal");

        return;
    }
}


/* =========================================================
   COPY PAYMENT NUMBER
========================================================= */

async function copyText(text){

    try{

        await navigator.clipboard.writeText(text);

        toast("Number copied!");

    }catch{

        toast(
            "Copy করা যায়নি",
            "error"
        );
    }
}


/* =========================================================
   COPY BUTTONS
========================================================= */

$$("[data-copy]").forEach(button=>{

    button.addEventListener("click",()=>{

        const value =
            button.dataset.copy;

        if(value){
            copyText(value);
        }

    });

});


/* =========================================================
   LIVE ORDER DEMO
========================================================= */

const demoLiveOrders = [

    {
        user:"Player***21",
        package:"115 Diamonds",
        status:"TOP-UP DONE"
    },

    {
        user:"Gamer***88",
        package:"Weekly",
        status:"TOP-UP DONE"
    },

    {
        user:"Ahsan***07",
        package:"610 Diamonds",
        status:"TOP-UP DONE"
    },

    {
        user:"FF***552",
        package:"240 Diamonds",
        status:"TOP-UP DONE"
    }

];


function renderDemoLiveOrders(){

    const container =
        $("#liveOrders");

    if(!container){
        return;
    }

    container.innerHTML =
        demoLiveOrders.map(order=>`

            <div class="live-order">

                <div class="order-user">

                    <div class="order-avatar">
                        🎮
                    </div>

                    <div class="order-info">

                        <strong>
                            ${escapeHTML(order.user)}
                        </strong>

                        <small>
                            ${escapeHTML(order.package)}
                        </small>

                    </div>

                </div>

                <span class="order-status">
                    ✓ ${escapeHTML(order.status)}
                </span>

            </div>

        `).join("");
}


/* =========================================================
   PAYMENT METHODS
========================================================= */

function setupPaymentMethod(){

    const select =
        $("#paymentMethod");

    if(!select){
        return;
    }

    select.addEventListener("change",()=>{

        const number =
            $("#paymentNumber");

        if(!number){
            return;
        }

        if(select.value === "bKash"){
            number.textContent =
                "01316897399";
        }

        else if(select.value === "Nagad"){
            number.textContent =
                "01410897399";
        }

        else if(select.value === "Upay"){
            number.textContent =
                "01316897399";
        }

        else{
            number.textContent =
                "Select payment method";
        }

    });
}


/* =========================================================
   SEARCH
========================================================= */

function setupSearch(){

    const search =
        $("#searchInput");

    if(!search){
        return;
    }

    search.addEventListener("input",()=>{

        const value =
            search.value.toLowerCase().trim();

        const cards =
            $$(".game-card,.package-card");

        cards.forEach(card=>{

            const text =
                card.textContent.toLowerCase();

            card.style.display =
                !value || text.includes(value)
                    ? ""
                    : "none";

        });

    });
}


/* =========================================================
   INITIALIZE
========================================================= */

document.addEventListener("DOMContentLoaded",async()=>{

    renderDemoLiveOrders();

    setupPaymentMethod();

    setupSearch();

    bindPackageButtons();

    await loadCurrentUser();

    await loadMyOrders();


    /* Login form */

    const loginForm =
        $("#loginForm");

    if(loginForm){
        loginForm.addEventListener(
            "submit",
            loginUser
        );
    }


    /* Register form */

    const registerForm =
        $("#registerForm");

    if(registerForm){
        registerForm.addEventListener(
            "submit",
            registerUser
        );
    }


    /* Order form */

    const orderForm =
        $("#orderForm");

    if(orderForm){
        orderForm.addEventListener(
            "submit",
            submitOrder
        );
    }


    /* Logout */

    $$("[data-logout]").forEach(button=>{

        button.addEventListener(
            "click",
            logoutUser
        );

    });


    /* Navigation */

    $$("[data-nav]").forEach(button=>{

        button.addEventListener("click",()=>{

            navigate(
                button.dataset.nav
            );

        });

    });

});


/* =========================================================
   GLOBAL FUNCTIONS
   index.html থেকে সরাসরি ব্যবহার করা যাবে
========================================================= */

window.openModal = openModal;
window.closeModal = closeModal;

window.showLogin = showLogin;
window.showRegister = showRegister;

window.loginUser = loginUser;
window.registerUser = registerUser;
window.logoutUser = logoutUser;

window.selectPackage = selectPackage;

window.submitOrder = submitOrder;

window.openOrders = openOrders;

window.navigate = navigate;

window.copyText = copyText;

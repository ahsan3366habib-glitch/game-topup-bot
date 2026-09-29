const packages = [
  {
    name: "Level Up-6",
    price: 50,
    type: "pass"
  },
  {
    name: "Level Up-10",
    price: 80,
    type: "pass"
  },
  {
    name: "Level Up-15",
    price: 80,
    type: "pass"
  },
  {
    name: "Level Up-20",
    price: 80,
    type: "pass"
  },
  {
    name: "Level Up-25",
    price: 80,
    type: "pass"
  },
  {
    name: "Level Up-30",
    price: 130,
    type: "pass"
  },

  {
    name: "Weekly Lite",
    price: 50,
    type: "membership"
  },
  {
    name: "Weekly Membership",
    price: 170,
    type: "membership"
  },
  {
    name: "Monthly Membership",
    price: 800,
    type: "membership"
  },

  {
    name: "25 Diamonds",
    price: 25,
    type: "diamond"
  },
  {
    name: "50 Diamonds",
    price: 40,
    type: "diamond"
  },
  {
    name: "115 Diamonds",
    price: 85,
    type: "diamond"
  },
  {
    name: "240 Diamonds",
    price: 165,
    type: "diamond"
  },
  {
    name: "610 Diamonds",
    price: 410,
    type: "diamond"
  },
  {
    name: "1240 Diamonds",
    price: 800,
    type: "diamond"
  },
  {
    name: "2530 Diamonds",
    price: 1600,
    type: "diamond"
  }
];


const packageBox = document.getElementById("packages");
const packageSelect = document.getElementById("package");


function renderPackages(type = "all") {

  packageBox.innerHTML = "";

  const list =
    type === "all"
      ? packages
      : packages.filter(item => item.type === type);


  list.forEach(item => {

    const card = document.createElement("div");

    card.className = "pack";

    card.innerHTML = `
      <h3>${item.name}</h3>

      <div class="price">
        ৳${item.price}
      </div>

      <button onclick="selectPackage('${item.name}')">
        Select
      </button>
    `;

    packageBox.appendChild(card);
  });


  updateSelect();
}


function updateSelect() {

  packageSelect.innerHTML =
    `<option value="">Select package</option>`;

  packages.forEach(item => {

    const option = document.createElement("option");

    option.value = item.name;

    option.textContent =
      `${item.name} — ৳${item.price}`;

    packageSelect.appendChild(option);
  });
}


function selectPackage(name) {

  packageSelect.value = name;

  document
    .getElementById("order")
    .scrollIntoView({
      behavior: "smooth"
    });
}


function filterPack(type, button) {

  document
    .querySelectorAll(".tab")
    .forEach(tab => {
      tab.classList.remove("active");
    });

  button.classList.add("active");

  renderPackages(type);
}


function showGame(game, button) {

  if (game !== "freefire") return;

  document
    .querySelectorAll(".game")
    .forEach(item => {
      item.classList.remove("active");
    });

  button.classList.add("active");

  document
    .getElementById("freefire")
    .scrollIntoView({
      behavior: "smooth"
    });
}


document
  .getElementById("orderForm")
  .addEventListener("submit", function(event) {

    event.preventDefault();


    const playerId =
      document.getElementById("playerId").value.trim();

    const selectedPackage =
      document.getElementById("package").value;

    const payment =
      document.getElementById("payment").value;

    const txn =
      document.getElementById("txn").value.trim();


    if (!playerId || !selectedPackage || !payment || !txn) {

      alert("সব তথ্য পূরণ করুন।");

      return;
    }


    const orderId =
      "TZ" +
      Date.now().toString().slice(-8);


    const result =
      document.getElementById("result");


    result.classList.remove("hidden");


    result.innerHTML = `
      <strong>✅ Order Submitted</strong>

      <br><br>

      Order ID:
      <b>${orderId}</b>

      <br>

      Player ID:
      <b>${playerId}</b>

      <br>

      Package:
      <b>${selectedPackage}</b>

      <br>

      Payment:
      <b>${payment}</b>

      <br>

      Txn ID:
      <b>${txn}</b>

      <br><br>

      আপনার payment manual verification-এর
      জন্য পাঠানো হয়েছে। Verification-এর পর
      top-up delivery করা হবে।

      <br><br>

      Support:
      <a href="https://t.me/Ahsanvai10"
         target="_blank">
         @Ahsanvai10
      </a>
    `;


    this.reset();

    result.scrollIntoView({
      behavior: "smooth"
    });

});


renderPackages("all");

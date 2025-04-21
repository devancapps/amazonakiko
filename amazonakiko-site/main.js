import { initializeApp } from "https://www.gstatic.com/firebasejs/10.10.0/firebase-app.js";
import { getFirestore, collection, getDocs } from "https://www.gstatic.com/firebasejs/10.10.0/firebase-firestore.js";
import { getStorage, ref, getDownloadURL } from "https://www.gstatic.com/firebasejs/10.10.0/firebase-storage.js";
import { firebaseConfig } from './firebase-config.js';

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const storage = getStorage(app);

const productGrid = document.getElementById("product-grid");

async function getImageUrl(imagePath) {
  try {
    const imageRef = ref(storage, imagePath);
    return await getDownloadURL(imageRef);
  } catch (error) {
    console.error("Error loading image:", error);
    return "https://via.placeholder.com/300x300?text=Image+Not+Available";
  }
}

async function loadProducts() {
  const productsRef = collection(db, "products");
  const snapshot = await getDocs(productsRef);

  for (const doc of snapshot.docs) {
    const data = doc.data();
    const imageUrl = await getImageUrl(`products/${doc.id}.jpg`);
    
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <img src="${imageUrl}" alt="${data.title}" loading="lazy">
      <h3>${data.title}</h3>
      <div class="price">${data.price}</div>
      <div class="rating">⭐ ${data.rating} | ${data.review_count} reviews</div>
      <button onclick="window.open('https://www.amazon.com/dp/${doc.id}?tag=87868584-20')">
        Buy Now
      </button>
    `;
    productGrid.appendChild(card);
  }
}

loadProducts(); 
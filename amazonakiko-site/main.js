import { initializeApp } from "https://www.gstatic.com/firebasejs/10.10.0/firebase-app.js";
import {
  getFirestore,
  collection,
  query,
  orderBy,
  limit,
  getDocs
} from "https://www.gstatic.com/firebasejs/10.10.0/firebase-firestore.js";
import { firebaseConfig } from './firebase-config.js';

// Initialize Firebase with error handling
let app;
let db;
try {
  app = initializeApp(firebaseConfig);
  db = getFirestore(app);
} catch (error) {
  console.error("Firebase initialization error:", error);
  document.getElementById("product-grid").innerHTML = `
    <div class="error-message">
      <p>Failed to initialize Firebase. Please try again later.</p>
    </div>
  `;
}

const productGrid = document.getElementById("product-grid");

function cleanTitle(rawTitle) {
  return rawTitle.split("$")[0].trim();
}

function formatNumber(numberString) {
  return Number(numberString.toString().replace(/,/g, "")).toLocaleString();
}

function isValidAmazonImage(url) {
  if (!url) return false;
  // Check for valid Amazon image domains
  return url.includes('images-na.ssl-images-amazon.com') || 
         url.includes('m.media-amazon.com') ||
         url.includes('images-amazon.com');
}

async function validateImageUrl(url) {
  if (!isValidAmazonImage(url)) return false;
  
  try {
    const response = await fetch(url, { method: 'HEAD' });
    return response.ok;
  } catch (error) {
    console.warn(`Image validation failed for ${url}:`, error);
    return false;
  }
}

function createCard(data, asin) {
  const card = document.createElement("div");
  card.className = "card";

  const title = cleanTitle(data.title || "");
  const price = data.price || "N/A";
  const rating = data.rating || "?";
  const reviews = formatNumber(data.review_count || "0");
  const isBestseller = data.source === "amazon_best_sellers";

  // Use a data URL for the placeholder to avoid CORS
  const placeholderImage = "data:image/svg+xml," + encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300">
      <rect width="300" height="300" fill="#f5f5f5"/>
      <text x="50%" y="50%" font-family="Arial" font-size="14" fill="#666" text-anchor="middle">
        No Image Available
      </text>
    </svg>
  `);

  card.innerHTML = `
    ${isBestseller ? '<div class="bestseller-badge">🔥 Bestseller</div>' : ''}
    <img 
      src="${data.image || placeholderImage}" 
      alt="${title}"
      loading="lazy"
      onerror="this.onerror=null; this.src='${placeholderImage}';"
    />
    <h3>${title}</h3>
    <div class="price">${price}</div>
    <div class="rating">⭐ ${rating} | ${reviews} reviews</div>
    <button onclick="window.open('https://www.amazon.com/dp/${asin}?tag=87868584-20')">Buy Now</button>
  `;
  return card;
}

function showLoading() {
  productGrid.innerHTML = `
    <div class="loading">
      <div class="loading-spinner"></div>
      <p>Loading deals...</p>
    </div>
  `;
}

function showNoProducts() {
  productGrid.innerHTML = `
    <div class="no-products">
      <p>No products found.</p>
      <button onclick="loadProducts()">Try Again</button>
    </div>
  `;
}

async function loadProducts() {
  if (!db) {
    console.error("Firestore not initialized");
    return;
  }

  showLoading();

  try {
    const q = query(
      collection(db, "products"),
      orderBy("timestamp", "desc"),
      limit(100)
    );
    const snapshot = await getDocs(q);
    
    // Filter products with valid Amazon images
    const validProducts = [];
    const validationPromises = [];
    
    snapshot.forEach(doc => {
      const data = doc.data();
      if (data.image) {
        validationPromises.push(
          validateImageUrl(data.image)
            .then(isValid => {
              if (isValid) {
                validProducts.push({ id: doc.id, data });
              }
            })
        );
      }
    });
    
    // Wait for all image validations to complete
    await Promise.all(validationPromises);

    if (validProducts.length === 0) {
      showNoProducts();
      return;
    }

    // Clear existing content
    productGrid.innerHTML = "";
    
    // Create a document fragment for better performance
    const fragment = document.createDocumentFragment();
    
    validProducts.forEach(({ id, data }) => {
      const card = createCard(data, id);
      fragment.appendChild(card);
    });
    
    productGrid.appendChild(fragment);
  } catch (error) {
    console.error("Error loading products:", error);
    productGrid.innerHTML = `
      <div class="error-message">
        <p>Failed to load products. Please try again later.</p>
        <button onclick="loadProducts()">Retry</button>
      </div>
    `;
  }
}

// Add styles
const style = document.createElement('style');
style.textContent = `
  .loading {
    text-align: center;
    padding: 2rem;
    width: 100%;
    color: #666;
  }
  
  .loading-spinner {
    width: 40px;
    height: 40px;
    margin: 0 auto 1rem;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #ff6f00;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .bestseller-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: #ff6f00;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.9rem;
    font-weight: 500;
  }
  
  .card {
    position: relative;
  }
  
  .card img {
    height: 200px;
    object-fit: contain;
    background: #f5f5f5;
  }
  
  .card h3 {
    height: 3em;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  
  @media (max-width: 768px) {
    #product-grid {
      grid-template-columns: 1fr;
      padding: 1rem;
    }
    
    .card {
      max-width: 100%;
    }
    
    .card img {
      height: 180px;
    }
  }
`;
document.head.appendChild(style);

// Load products when the page loads
document.addEventListener('DOMContentLoaded', loadProducts); 
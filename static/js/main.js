document.addEventListener("DOMContentLoaded", () => {
    fetchOptions();
});

// Track if charts are initialized
let analyticsLoaded = false;

function switchTab(tabId) {
    // Hide all sections
    document.querySelectorAll('section').forEach(el => el.classList.add('hidden-section'));
    
    // Show active section
    document.getElementById(`${tabId}-section`).classList.remove('hidden-section');
    
    // Update button styling
    document.querySelectorAll('aside button').forEach(btn => {
        btn.classList.remove('bg-indigo-600', 'text-white', 'shadow-lg', 'shadow-indigo-900/20');
        btn.classList.add('text-slate-400');
    });
    
    const activeBtn = document.getElementById(`tab-${tabId}`);
    activeBtn.classList.remove('text-slate-400');
    activeBtn.classList.add('bg-indigo-600', 'text-white', 'shadow-lg', 'shadow-indigo-900/20');

    // DOM Rendering Fix: Wait for the browser layout to reflow before rendering charts
    if (tabId === 'analytics') {
        if (!analyticsLoaded) {
            setTimeout(() => {
                loadAnalytics();
                analyticsLoaded = true;
            }, 100); // 100ms delay ensures 'display: block' has taken effect
        } else {
            // If returning to the tab, trigger window resize so Plotly auto-adjusts
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 50);
        }
    }
}

// --- Fetch Dropdown Options ---
async function fetchOptions() {
    try {
        const response = await fetch('/api/options');
        const data = await response.json();
        
        const populate = (id, arr) => {
            const el = document.getElementById(id);
            if(el) { el.innerHTML = arr.map(val => `<option value="${val}">${val}</option>`).join(''); }
        };

        populate('p_sector', data.sectors);
        populate('p_bed', data.bedrooms);
        populate('p_bath', data.bathrooms);
        populate('p_balc', data.balconies);
        populate('p_age', data.property_age);
        populate('p_furnish', data.furnishing_type);
        populate('p_luxury', data.luxury_category);
        populate('p_floor', data.floor_category);
        
        populate('r_location', data.locations);
        populate('r_apartment', data.apartments);
        populate('plot-pie-select', data.analytics_sectors);
    } catch (error) {
        console.error("Failed to fetch options", error);
    }
}

// --- Price Predictor ---
document.getElementById('predict-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btnText = document.getElementById('predict-text');
    const spinner = document.getElementById('predict-spinner');
    
    btnText.textContent = 'Calculating...';
    spinner.classList.remove('hidden');

    const payload = {
        property_type: document.getElementById('p_type').value,
        sector: document.getElementById('p_sector').value,
        bedrooms: document.getElementById('p_bed').value,
        bathroom: document.getElementById('p_bath').value,
        balcony: document.getElementById('p_balc').value,
        property_age: document.getElementById('p_age').value,
        built_up_area: document.getElementById('p_area').value,
        servant_room: document.getElementById('p_servant').value,
        store_room: document.getElementById('p_store').value,
        furnishing_type: document.getElementById('p_furnish').value,
        luxury_category: document.getElementById('p_luxury').value,
        floor_category: document.getElementById('p_floor').value,
    };

    try {
        const res = await fetch('/api/predict', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if(data.status === 'success') {
            document.getElementById('prediction-result').classList.remove('hidden');
            document.getElementById('price-output').innerText = `${data.low} - ${data.high}`;
        } else {
            alert('Prediction failed: ' + data.message);
        }
    } catch (err) { alert('Network Error'); }
    
    btnText.textContent = 'Predict Price';
    spinner.classList.add('hidden');
});

// --- Analytics Section ---
function loadAnalytics() {
    const config = { responsive: true, displayModeBar: false };
    
    fetch('/api/analytics/geomap')
        .then(async res => {
            // Check if Flask returned our 400 error JSON
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.message || 'Backend crashed');
            }
            return res.json(); // Safely parse the map data
        })
        .then(fig => {
            Plotly.newPlot('plot-geomap', fig.data, fig.layout, config).then(() => {
                window.dispatchEvent(new Event('resize'));
            });
        })
        .catch(err => {
            console.error("Geomap Backend Error:", err.message);
            // Visually display the error inside the box instead of just a blank screen
            document.getElementById('plot-geomap').innerHTML = 
                `<div class="flex items-center justify-center h-full text-red-400 font-medium">Map Error: ${err.message}</div>`;
        });

    loadScatterPlot();
    loadPieChart();

    fetch('/api/analytics/wordcloud')
        .then(res => res.json())
        .then(data => document.getElementById('plot-wordcloud').src = 'data:image/png;base64,' + data.image);

    fetch('/api/analytics/distplot')
        .then(res => res.json())
        .then(data => document.getElementById('plot-distplot').src = 'data:image/png;base64,' + data.image);
}

function loadScatterPlot() {
    const type = document.getElementById('plot-scatter-select').value;
    fetch(`/api/analytics/scatter?property_type=${type}`)
        .then(res => res.json())
        .then(fig => Plotly.react('plot-scatter', fig.data, fig.layout, { responsive: true, displayModeBar: false }));
}

function loadPieChart() {
    const sector = document.getElementById('plot-pie-select').value;
    fetch(`/api/analytics/pie?sector=${sector}`)
        .then(res => res.json())
        .then(fig => Plotly.react('plot-pie', fig.data, fig.layout, { responsive: true, displayModeBar: false }));
}


// --- Recommender Section ---
document.getElementById('radius-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        location: document.getElementById('r_location').value,
        radius: document.getElementById('r_radius').value
    };
    
    const res = await fetch('/api/recommend/search', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    
    const container = document.getElementById('radius-results');
    container.innerHTML = '';
    // Dark mode radius result cards
    data.results.forEach(item => {
        container.innerHTML += `<div class="bg-slate-700/50 border border-slate-600 text-white p-3 rounded-xl text-center font-medium shadow-sm transition hover:bg-slate-700"><span class="block truncate">${item.name}</span><span class="text-xs text-indigo-400 mt-1 block tracking-widest uppercase">${item.distance} Kms</span></div>`;
    });
    container.classList.remove('hidden');
});

document.getElementById('recommend-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = { apartment: document.getElementById('r_apartment').value };
    
    const res = await fetch('/api/recommend/apartments', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    
    if(data.status === 'success') {
        const tbody = document.getElementById('recommend-tbody');
        tbody.innerHTML = '';
        // Dark mode table rows
        data.results.forEach((item, index) => {
            const bgClass = index % 2 === 0 ? 'bg-slate-800' : 'bg-slate-850';
            tbody.innerHTML += `<tr class="${bgClass} hover:bg-slate-700 transition-colors"><td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">${item.property}</td><td class="px-6 py-4 whitespace-nowrap text-sm text-indigo-400 font-semibold">${item.score}</td></tr>`;
        });
        document.getElementById('recommend-table-container').classList.remove('hidden');
    }
});
async function predict() {
    const selectedFood = document.getElementById('food_select').value;
    const manualFoodName = document.getElementById('food_manual_name').value;

    const payload = {
        gender: document.getElementById('gender').value,
        age: parseFloat(document.getElementById('age').value || 0),
        weight: parseFloat(document.getElementById('weight').value || 0),
        waist_circumference: parseFloat(document.getElementById('wc').value || 0),
        birth_place: document.getElementById('birth_place').value,
        blood_group: document.getElementById('blood_group').value,
        family_history: document.getElementById('family_history').value,
        physical_activity: document.getElementById('physical_activity').value,
        food_item: (manualFoodName && manualFoodName.trim()) ? manualFoodName.trim() : (selectedFood || ''),
        carb: parseFloat(document.getElementById('carb').value || 0),
        protein: parseFloat(document.getElementById('protein').value || 0),
        fat: parseFloat(document.getElementById('fat').value || 0),
        dietary_fiber: parseFloat(document.getElementById('fiber').value || 0)
    };

    const resEl = document.getElementById('result');
    const resContent = document.getElementById('result-content');
    const predictBtn = document.getElementById('predict');

    // Show loading state
    predictBtn.disabled = true;
    predictBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Predicting...';
    resEl.classList.remove('d-none');
    resEl.classList.remove('alert-success', 'alert-warning', 'alert-danger', 'alert-info');
    resEl.classList.add('alert-info');
    resContent.innerHTML = '<strong>Processing your request...</strong>';

    try {
        // Use explicit origin so this works when the static files are served
        // from a different base path or when the page is loaded from a file.
        if (location.protocol !== 'http:' && location.protocol !== 'https:') {
            throw new Error('This page is not served over HTTP. Please run the server and open the app at http://127.0.0.1:8000/');
        }
        const url = (window.location && window.location.origin ? window.location.origin : '') + '/api/predict';
        console.log('Sending predict request to', url, 'payload:', payload);

        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!resp.ok) {
            // Try to get server error details (text) when available
            let txt = '';
            try { txt = await resp.text(); } catch (e) { /* ignore */ }
            throw new Error('Server error ' + resp.status + (txt ? (': ' + txt) : ''));
        }

        // Parse JSON safely
        let data;
        try {
            data = await resp.json();
        } catch (e) {
            const txt = await resp.text().catch(() => '');
            throw new Error('Invalid JSON response from server' + (txt ? (': ' + txt) : ''));
        }

        const ppgiValue = data && (data.ppgi ?? data.ppgi_value ?? null);
        if (ppgiValue === null || ppgiValue === undefined) {
            throw new Error('Server did not return ppgi in response');
        }

        // Determine alert type based on GI value bands
        // Low (0–55) = green, Medium (56–69) = orange, High (70+) = red
        let alertType = 'alert-success';
        let interpretation = 'Low GI (0–55) – slow rise in blood sugar';

        if (ppgiValue >= 70) {
            alertType = 'alert-danger';
            interpretation = 'High GI (70+) – rapid rise in blood sugar';
        } else if (ppgiValue >= 56) {
            alertType = 'alert-warning';
            interpretation = 'Medium GI (56–69) – moderate rise in blood sugar';
        }

        resEl.classList.remove('alert-info');
        resEl.classList.add(alertType);

        const iaucInfo = (data && (data.iauc_food != null) && (data.iauc_glucose_ref != null))
            ? `<p class="mb-0 text-muted small">IAUC (food): ${data.iauc_food} | IAUC (glucose ref): ${data.iauc_glucose_ref}</p>`
            : '';

        resContent.innerHTML = `
            <div>
                <h5 class="alert-heading mb-2">Prediction Result</h5>
                <p class="mb-2"><strong>Predicted PPGI:</strong> <span class="fs-4 fw-bold">${ppgiValue}</span></p>
                <p class="mb-1"><em>${interpretation}</em></p>
                ${iaucInfo}
            </div>
        `;
        // Ensure the result is visible to the user
        try { resEl.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (_) { }
    } catch (err) {
        console.error('Prediction failed:', err);
        resEl.classList.remove('alert-info');
        resEl.classList.add('alert-danger');
        // Show friendly message and the error details
        resContent.innerHTML = `<strong>Error:</strong> ${err.message}`;
        try { resEl.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (_) { }
    } finally {
        // Reset button state
        predictBtn.disabled = false;
        predictBtn.innerHTML = '<i class="bi bi-lightning-charge-fill"></i> Predict PPGI';
    }
}

// Log to verify script loaded
console.log('PPGI script loaded');

// Ensure click handler is attached whether or not DOMContentLoaded already fired
function onReady(fn) {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fn);
    } else {
        fn();
    }
}

onReady(() => {
    const btn = document.getElementById('predict');
    if (btn) {
        btn.addEventListener('click', predict);
        console.log('Predict button handler attached');
    } else {
        console.log('Predict button not found in DOM');
    }
});

// --- Food data and autofill (only user-provided items) ---
const FOOD_DATA = {
    "glucose_solution": { label: "Glucose Solution", "Carb": 100, "Protein": 0, "Fat": 0, "Dietary fiber": 0 },
    "rice_super_kernel": { label: "Rice - Super kernel", "Carb": 28, "Protein": 2.7, "Fat": 0.3, "Dietary fiber": 0.4 },
    "rathu_suduru": { label: "Rathu Suduru", "Carb": 26, "Protein": 2.4, "Fat": 0.7, "Dietary fiber": 1.2 },
    "garlic_bee_honey": { label: "Garlic - Bee honey", "Carb": 82, "Protein": 0.3, "Fat": 0, "Dietary fiber": 0.2 },
    "white_bread": { label: "White Bread", "Carb": 49, "Protein": 8, "Fat": 3.2, "Dietary fiber": 2.7 },
    "kurakkan_bread": { label: "Kurakkan Bread", "Carb": 45, "Protein": 7, "Fat": 5, "Dietary fiber": 4 }
};

function populateFoodDropdown() {
    const sel = document.getElementById('food_select');
    // Replace existing options so only the provided items remain
    sel.innerHTML = '<option value="">-- Select a food --</option>';
    Object.entries(FOOD_DATA).forEach(([key, obj]) => {
        const opt = document.createElement('option');
        opt.value = key;
        opt.textContent = obj.label || key;
        sel.appendChild(opt);
    });
}

function autofillFromFood(name) {
    if (!name || !FOOD_DATA[name]) return;
    const d = FOOD_DATA[name];
    document.getElementById('carb').value = d.Carb;
    document.getElementById('protein').value = d.Protein;
    document.getElementById('fat').value = d.Fat;
    document.getElementById('fiber').value = d['Dietary fiber'];
}

document.getElementById('food_select').addEventListener('change', (e) => {
    const name = e.target.value;
    if (name) {
        autofillFromFood(name);
        document.getElementById('food_manual_name').style.display = 'none';
        document.getElementById('manual_toggle').checked = false;
    }
});

document.getElementById('manual_toggle').addEventListener('change', (e) => {
    const manual = e.target.checked;
    document.getElementById('food_manual_name').style.display = manual ? 'block' : 'none';
    if (manual) {
        document.getElementById('food_select').value = '';
        // Clear nutritional values for manual entry
        document.getElementById('carb').value = 0;
        document.getElementById('protein').value = 0;
        document.getElementById('fat').value = 0;
        document.getElementById('fiber').value = 0;
    }
});

// Initialize
populateFoodDropdown();

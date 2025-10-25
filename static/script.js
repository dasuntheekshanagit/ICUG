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
        portion_g: parseFloat(document.getElementById('portion').value || 100),
        nutrients_per_serving: Boolean(document.getElementById('nutrients_per_serving') && document.getElementById('nutrients_per_serving').checked),
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
        const glValue = data && (data.gl ?? null);
        if (ppgiValue === null || ppgiValue === undefined) {
            throw new Error('Server did not return ppgi in response');
        }

        // Determine alert type and badges based on GI value bands
        // Low (0–55) = green, Medium (56–69) = yellow, High (70+) = red
        let alertType = 'alert-success';
        let interpretation = 'Low GI (0–55) – slow rise in blood sugar';
        let giBadge = 'bg-success';
        let giBandText = 'Low';
        if (ppgiValue >= 70) {
            alertType = 'alert-danger';
            giBadge = 'bg-danger';
            giBandText = 'High';
            interpretation = 'High GI (70+) – rapid rise in blood sugar';
        } else if (ppgiValue >= 56) {
            alertType = 'alert-warning';
            giBadge = 'bg-warning text-dark';
            giBandText = 'Medium';
            interpretation = 'Medium GI (56–69) – moderate rise in blood sugar';
        }

        // GL bands: Low <10, Medium 11–19, High 20+
        let glBadge = 'bg-success';
        let glBandText = 'Low';
        if (glValue !== null && glValue !== undefined) {
            if (glValue >= 20) {
                glBadge = 'bg-danger';
                glBandText = 'High';
            } else if (glValue >= 11) {
                glBadge = 'bg-warning text-dark';
                glBandText = 'Medium';
            }
        }

        resEl.classList.remove('alert-info');
        resEl.classList.add(alertType);

        const iaucFood = (data && data.iauc_food != null) ? data.iauc_food : null;
        const iaucGlu = (data && data.iauc_glucose_ref != null) ? data.iauc_glucose_ref : null;

        resContent.innerHTML = `
            <div class="mb-2">
                <h5 class="alert-heading mb-2">Prediction Result</h5>
            </div>
            <div class="row g-3">
                <div class="col-md-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-body text-center">
                            <div class="text-muted small mb-1">IAUC (food)</div>
                            <div class="fs-2 fw-bold">${iaucFood !== null ? iaucFood : '—'}</div>
                            ${iaucGlu !== null ? `<div class="text-muted small">IAUC (glucose ref): ${iaucGlu}</div>` : ''}
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-body text-center">
                            <div class="text-muted small mb-1">GI</div>
                            <div class="fs-2 fw-bold">${ppgiValue}</div>
                            <span class="badge ${giBadge}">${giBandText}</span>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-body text-center">
                            <div class="text-muted small mb-1">GL</div>
                            <div class="fs-2 fw-bold">${glValue !== null && glValue !== undefined ? glValue : '—'}</div>
                            ${glValue !== null && glValue !== undefined ? `<span class="badge ${glBadge}">${glBandText}</span>` : ''}
                        </div>
                    </div>
                </div>
            </div>
            <p class="mt-3 mb-0"><em>${interpretation}</em></p>
        `;
        // Reveal download button now that we have a saved last result
        const dl = document.getElementById('download-csv');
        if (dl) dl.classList.remove('d-none');
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

// --- Food data and autofill (only foods from the provided list) ---
const FOOD_DATA = {
    "glucose_solution": { label: "Glucose Solution", "Carb": 100.00, "Protein": 0.00, "Fat": 0.00, "Dietary fiber": 0.00 },
    "rice_super_kernal": { label: "Rice-Super kernal", "Carb": 81.70, "Protein": 3.70, "Fat": 1.10, "Dietary fiber": 5.40 },
    "rice_red_fragrant": { label: "Rice-Red Fragrant", "Carb": 79.30, "Protein": 4.90, "Fat": 1.80, "Dietary fiber": 5.00 },
    "rice_purple_queen": { label: "Rice-Purple queen", "Carb": 78.80, "Protein": 7.40, "Fat": 1.00, "Dietary fiber": 7.60 },
    "rice_rathu_suduru": { label: "Rice-Rathu Suduru", "Carb": 80.30, "Protein": 3.70, "Fat": 1.30, "Dietary fiber": 6.60 },
    "bee_honey": { label: "Bee-Honey", "Carb": 79.90, "Protein": 0.20, "Fat": 0.00, "Dietary fiber": 0.00 },
    "garlic_bee_honey_73": { label: "Garlic-Bee honey Product (73)", "Carb": 73.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "garlic_bee_honey_74": { label: "Garlic-Bee honey Product (74)", "Carb": 74.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "garlic_bee_honey_75": { label: "Garlic-Bee honey Product (75)", "Carb": 75.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "garlic_bee_honey_76": { label: "Garlic-Bee honey Product (76)", "Carb": 76.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "garlic_bee_honey_77": { label: "Garlic-Bee honey Product (77)", "Carb": 77.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "garlic_bee_honey_78": { label: "Garlic-Bee honey Product (78)", "Carb": 78.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "garlic_bee_honey_79": { label: "Garlic-Bee honey Product (79)", "Carb": 79.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "garlic_bee_honey_80": { label: "Garlic-Bee honey Product (80)", "Carb": 80.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "garlic_bee_honey_81": { label: "Garlic-Bee honey Product (81)", "Carb": 81.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "garlic_bee_honey_82": { label: "Garlic-Bee honey Product (82)", "Carb": 82.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "garlic_bee_honey_83": { label: "Garlic-Bee honey Product (83)", "Carb": 83.00, "Protein": 1.60, "Fat": 0.00, "Dietary fiber": 1.00 },
    "basmati_red_fragrant": { label: "Basmati-Red Fragrant", "Carb": 76.70, "Protein": 9.70, "Fat": 1.87, "Dietary fiber": 2.50 },
    "basmati_ceylon_purple": { label: "Basmati-Ceylon Purple Rice", "Carb": 75.23, "Protein": 10.40, "Fat": 1.80, "Dietary fiber": 5.20 },
    "basmati_cic_super_kernel": { label: "Basmati-CIC super kernel", "Carb": 78.30, "Protein": 10.95, "Fat": 1.65, "Dietary fiber": 1.70 },
    "basmati_ceylon_purple_dup": { label: "Basmati-Ceylon Purple Rice (variant)", "Carb": 75.23, "Protein": 10.40, "Fat": 1.80, "Dietary fiber": 1.70 },
    "basmati_red_fragrant_dup": { label: "Basmati-Red Fragrant (variant)", "Carb": 75.23, "Protein": 10.40, "Fat": 1.80, "Dietary fiber": 2.50 },
    "red_fragrance_string_hoppers": { label: "Red Fragrance String Hoppers", "Carb": 69.40, "Protein": 10.35, "Fat": 2.16, "Dietary fiber": 0.45 },
    "white_basmati_string_hoppers": { label: "White Basmati String Hoppers", "Carb": 78.07, "Protein": 7.73, "Fat": 0.90, "Dietary fiber": 0.52 },
    "sticky_basmati_string_hoppers": { label: "Sticky Basmati String Hoppers", "Carb": 80.21, "Protein": 3.41, "Fat": 0.23, "Dietary fiber": 0.15 },
    "mdk_string_hoppers": { label: "MDK String Hoppers", "Carb": 76.09, "Protein": 5.02, "Fat": 0.02, "Dietary fiber": 0.07 },
    "white_bread": { label: "White Bread", "Carb": 59.10, "Protein": 8.10, "Fat": 2.40, "Dietary fiber": 2.10 },
    "kurakkan_bread": { label: "Kurakkan Bread", "Carb": 49.40, "Protein": 7.20, "Fat": 3.20, "Dietary fiber": 3.10 },
    "multigrain_bread": { label: "Multigrain Bread", "Carb": 55.60, "Protein": 5.40, "Fat": 4.80, "Dietary fiber": 3.40 },
    "soup": { label: "Soup", "Carb": 26.46, "Protein": 9.76, "Fat": 6.74, "Dietary fiber": 49.04 },
    "savandara_mix": { label: "Savandara Mix", "Carb": 73.35, "Protein": 7.85, "Fat": 1.25, "Dietary fiber": 4.05 },
    "diyabath_savandari_mix": { label: "Diyabath- Savandari Mix", "Carb": 11.22, "Protein": 1.46, "Fat": 2.72, "Dietary fiber": 0.67 },
    "fried_rice_super_kernal": { label: "Fried Rice-Super kernal", "Carb": 27.75, "Protein": 3.85, "Fat": 6.80, "Dietary fiber": 1.90 },
    "rice_porridge": { label: "Rice Porridge", "Carb": 10.73, "Protein": 1.24, "Fat": 1.99, "Dietary fiber": 0.76 },
    "kiribath_savandari_mix": { label: "Kiribath- Savandari Mix", "Carb": 20.05, "Protein": 2.25, "Fat": 2.05, "Dietary fiber": 1.05 },
    "string_hopper_rfb_coconut": { label: "String hopper-RFB & Coconut Gravy", "Carb": 26.34, "Protein": 2.43, "Fat": 3.49, "Dietary fiber": 0.27 },
    "kiribath_katta_sambal": { label: "Kiribath+katta sambal", "Carb": 19.38, "Protein": 3.14, "Fat": 2.00, "Dietary fiber": 1.39 },
    "red_fragrance_broken": { label: "Red Fragrance Broken", "Carb": 10.73, "Protein": 1.24, "Fat": 1.99, "Dietary fiber": 0.76 },
    "embul_mid_ripen": { label: "Embul-Mid ripen", "Carb": 25.68, "Protein": 1.67, "Fat": 0.14, "Dietary fiber": 2.09 },
    "kolikuttu_mid_ripen": { label: "Kolikuttu-Mid Ripen", "Carb": 25.75, "Protein": 1.32, "Fat": 0.17, "Dietary fiber": 2.20 },
    "kolikuttu_ripen": { label: "Kolikuttu-Ripen", "Carb": 23.67, "Protein": 0.96, "Fat": 0.20, "Dietary fiber": 5.30 },
    "seeni_mid_ripen": { label: "Seeni-Mid Ripen", "Carb": 27.61, "Protein": 1.77, "Fat": 0.18, "Dietary fiber": 1.97 },
    "seeni_ripen": { label: "Seeni-Ripen", "Carb": 28.96, "Protein": 1.48, "Fat": 0.05, "Dietary fiber": 3.10 }
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

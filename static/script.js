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
        const resp = await fetch('/api/predict', {
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!resp.ok) throw new Error('Server error ' + resp.status);
        
        const data = await resp.json();
        const ppgiValue = data.ppgi;
        
        // Determine alert type based on PPGI value
        let alertType = 'alert-success';
        let interpretation = 'Low glycemic response - Good for blood sugar control';
        
        if (ppgiValue > 70) {
            alertType = 'alert-danger';
            interpretation = 'High glycemic response - May cause rapid blood sugar spike';
        } else if (ppgiValue > 55) {
            alertType = 'alert-warning';
            interpretation = 'Medium glycemic response - Moderate impact on blood sugar';
        }
        
        resEl.classList.remove('alert-info');
        resEl.classList.add(alertType);
        
        resContent.innerHTML = `
            <div>
                <h5 class="alert-heading mb-2">Prediction Result</h5>
                <p class="mb-2"><strong>Predicted PPGI:</strong> <span class="fs-4 fw-bold">${ppgiValue}</span></p>
                <p class="mb-0"><em>${interpretation}</em></p>
            </div>
        `;
    } catch (err) {
        console.error(err);
        resEl.classList.remove('alert-info');
        resEl.classList.add('alert-danger');
        resContent.innerHTML = `<strong>Error:</strong> ${err.message}`;
    } finally {
        // Reset button state
        predictBtn.disabled = false;
        predictBtn.innerHTML = '<i class="bi bi-lightning-charge-fill"></i> Predict PPGI';
    }
}

document.getElementById('predict').addEventListener('click', predict);

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

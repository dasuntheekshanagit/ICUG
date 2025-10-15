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
    resEl.textContent = 'Predicting...';

    try {
        const resp = await fetch('/api/predict', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!resp.ok) throw new Error('Server error ' + resp.status);
        const data = await resp.json();
        resEl.innerHTML = `<strong>PPGI:</strong> ${data.ppgi}<pre style="max-height:200px;overflow:auto">${JSON.stringify(data.input_summary, null, 2)}</pre>`;
    } catch (err) {
        console.error(err);
        resEl.textContent = 'Prediction failed: ' + err.message;
    }
}

document.getElementById('predict').addEventListener('click', predict);

// --- Food data and autofill ---
const FOOD_DATA = {
    "Apple": { "Carb": 14, "Protein": 0.3, "Fat": 0.2, "Dietary fiber": 2.4 },
    "Banana": { "Carb": 23, "Protein": 1.1, "Fat": 0.3, "Dietary fiber": 2.6 },
    "Chicken Breast": { "Carb": 0, "Protein": 31, "Fat": 3.6, "Dietary fiber": 0 },
    "Brown Rice": { "Carb": 23, "Protein": 2.7, "Fat": 0.9, "Dietary fiber": 3.5 },
    "Broccoli": { "Carb": 7, "Protein": 2.8, "Fat": 0.4, "Dietary fiber": 2.6 }
};

function populateFoodDropdown() {
    const sel = document.getElementById('food_select');
    Object.keys(FOOD_DATA).forEach(name => {
        const opt = document.createElement('option'); opt.value = name; opt.textContent = name; sel.appendChild(opt);
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
    if (manual) { document.getElementById('food_select').value = ''; }
});

// Initialize
populateFoodDropdown();

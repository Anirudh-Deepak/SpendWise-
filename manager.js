// manager.js

const totalSpentEl = document.getElementById("totalSpent");
const suggestedSavingsEl = document.getElementById("suggestedSavings");

const suggestions = [
  "Cut down on eating out – cook at home more often.",
  "Cancel unused subscriptions.",
  "Use public transport instead of cabs.",
  "Track daily expenses to spot wasteful spending.",
  "Save at least 20% of income before spending."
];

const MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
];

let allBankData = []; // To store all parsed data

function updateDashboard(totalSpent, year, monthName) {
    totalSpentEl.textContent = `$${totalSpent.toFixed(2)}`;
    let savings = totalSpent * 0.2;
    suggestedSavingsEl.textContent = `$${savings.toFixed(2)}`;

    // Update the header
    document.querySelector('.main-area h2').textContent = `Monthly Summary (${monthName} ${year})`;

    // Show random tip
    let tip = suggestions[Math.floor(Math.random() * suggestions.length)];
    document.getElementById("tipBox").innerHTML = `<h3>💡 Saving Tip:</h3><p>${tip}</p>`;
}

// Populate year and month selectors based on data
function initializePeriodSelectors() {
    const yearSelect = document.getElementById("yearSelect");
    const monthSelect = document.getElementById("monthSelect");
    
    yearSelect.innerHTML = '';
    
    // Populate Years
    const uniqueYears = [...new Set(allBankData.map(d => d.Year))].sort((a, b) => b - a);
    uniqueYears.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    });
    
    // Populate Months (static list)
    monthSelect.innerHTML = MONTH_NAMES.map(month => `<option value="${month}">${month}</option>`).join('');

    // Set default period to the latest month
    if (uniqueYears.length > 0) {
        const latestYear = uniqueYears[0];
        const latestMonth = Math.max(...allBankData.filter(d => d.Year === latestYear).map(d => d.Month));
        
        yearSelect.value = latestYear;
        monthSelect.value = MONTH_NAMES[latestMonth - 1]; 
    }
}

// Filter data and calculate total spent for the selected period
function filterAndRender() {
    const yearSelect = document.getElementById("yearSelect");
    const monthSelect = document.getElementById("monthSelect");
    
    if (yearSelect.value === '' || monthSelect.value === '') {
        updateDashboard(0, 'N/A', 'N/A');
        return;
    }
    
    const year = parseInt(yearSelect.value);
    const monthName = monthSelect.value;
    const month = MONTH_NAMES.indexOf(monthName) + 1; // 1-12

    const currentFilteredData = allBankData.filter(d => d.Year === year && d.Month === month);
    
    // Calculate total spending (excluding Income and Savings from 'spent')
    const totalSpent = currentFilteredData
        .filter(d => d.Amount > 0 && d.Category !== 'Income' && d.Category !== 'Savings')
        .reduce((sum, d) => sum + d.Amount, 0);

    updateDashboard(totalSpent, year, monthName);
}


document.addEventListener("DOMContentLoaded", () => {
    const savedData = localStorage.getItem("bankData");
    
    if (savedData) {
        try {
            allBankData = JSON.parse(savedData).map(row => {
                const dateObj = new Date(row.Date);
                row.Year = dateObj.getFullYear();
                row.Month = dateObj.getMonth() + 1;
                return row;
            });

            if (allBankData.length > 0) {
                initializePeriodSelectors();
                filterAndRender(); // Initial render with default latest month
                
                // Attach event listeners for dynamic updates
                document.getElementById("yearSelect").addEventListener("change", filterAndRender);
                document.getElementById("monthSelect").addEventListener("change", filterAndRender);
                
            } else {
                // Handle no data case
                updateDashboard(0, 'N/A', 'N/A');
                document.getElementById('tipBox').innerHTML = `<h3>💡 Saving Tip:</h3><p>Please upload a bank statement on the home page to see your summary!</p>`;
            }
        } catch (error) {
            console.error("Error loading or parsing data:", error);
            updateDashboard(0, 'Error', 'Loading');
            document.getElementById('tipBox').innerHTML = `<h3>💡 Saving Tip:</h3><p>An error occurred loading your data.</p>`;
        }
    } else {
        // No data in localStorage
        updateDashboard(0, 'N/A', 'N/A');
        document.getElementById('tipBox').innerHTML = `<h3>💡 Saving Tip:</h3><p>Please upload a bank statement on the home page to see your summary!</p>`;
    }
});
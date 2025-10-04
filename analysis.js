// analysis.js

// Month names mapping
const MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June", 
    "July", "August", "September", "October", "November", "December"
];

let allBankData = []; // To store all parsed data
let currentFilteredData = []; // Data for the currently selected period

// Utility function to determine the week number of the month
function getWeekOfMonth(date) {
    const dayOfMonth = date.getDate();
    return Math.ceil(dayOfMonth / 7);
}

// Load saved bank statement and initialize dashboard
document.addEventListener("DOMContentLoaded", () => {
    const savedData = localStorage.getItem("bankData");
    if (savedData) {
        try {
            allBankData = JSON.parse(savedData).map(row => {
                // Pre-process and enhance data
                const dateObj = new Date(row.Date);
                row.DateObj = dateObj;
                row.Year = dateObj.getFullYear();
                row.Month = dateObj.getMonth() + 1; // 1-12
                row.WeekOfMonth = getWeekOfMonth(dateObj);
                return row;
            });

            if (allBankData.length > 0) {
                initializePeriodSelectors();
                
                // Set default period to the latest month
                const yearSelect = document.getElementById("yearSelect");
                const monthSelect = document.getElementById("monthSelect");
                const latestYear = Math.max(...allBankData.map(d => d.Year));
                const latestMonth = Math.max(...allBankData.filter(d => d.Year === latestYear).map(d => d.Month));
                
                yearSelect.value = latestYear;
                monthSelect.value = MONTH_NAMES[latestMonth - 1]; // Set by name
                
                filterAndRender();
            }
        } catch (error) {
            console.error("Error parsing bankData from localStorage:", error);
            document.querySelector('.main-area').innerHTML = '<p class="card">Error loading data. Please re-upload your statement.</p>';
        }
    } else {
        document.querySelector('.main-area').innerHTML = '<p class="card">No bank statement uploaded. Please go to Home and upload a CSV file.</p>';
    }
    
    // Attach event listeners after selectors are populated
    document.getElementById("yearSelect").addEventListener("change", filterAndRender);
    document.getElementById("monthSelect").addEventListener("change", filterAndRender);
});

// Populate year and month selectors based on data
function initializePeriodSelectors() {
    const yearSelect = document.getElementById("yearSelect");
    
    // Clear existing options (from HTML template)
    yearSelect.innerHTML = '';
    
    // Populate Years
    const uniqueYears = [...new Set(allBankData.map(d => d.Year))].sort((a, b) => b - a);
    uniqueYears.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelect.appendChild(option);
    });
}


// Filter data and render all components
function filterAndRender() {
    const year = parseInt(document.getElementById("yearSelect").value);
    const monthName = document.getElementById("monthSelect").value;
    const month = MONTH_NAMES.indexOf(monthName) + 1; // 1-12

    currentFilteredData = allBankData.filter(d => d.Year === year && d.Month === month);
    
    renderTable(currentFilteredData);
    renderPieChart(currentFilteredData);
    renderWeeklyGraph(currentFilteredData);
}


// Render statement table
function renderTable(data) {
    const table = document.getElementById("statementTable");
    table.innerHTML = "";

    if (!data || data.length === 0) {
        table.innerHTML = "<thead><tr><th>Date</th><th>Category</th><th>Amount</th></tr></thead><tbody><tr><td colspan='3'>No data available for this period.</td></tr></tbody>";
        return;
    }

    // Header (assuming keys are consistent: Date, Category, Amount)
    const headers = Object.keys(data[0]).filter(key => ['Date', 'Category', 'Amount'].includes(key));
    let headerHtml = "<thead><tr>";
    headers.forEach(h => {
        headerHtml += `<th>${h}</th>`;
    });
    headerHtml += "</tr></thead>";
    
    // Rows
    let rowsHtml = "<tbody>";
    data.forEach(row => {
        let rowHtml = "<tr>";
        headers.forEach(h => {
            let cellContent = row[h];
            if (h === 'Amount') {
                cellContent = `$${row[h].toFixed(2)}`;
            }
            rowHtml += `<td>${cellContent}</td>`;
        });
        rowHtml += "</tr>";
        rowsHtml += rowHtml;
    });
    rowsHtml += "</tbody>";

    table.innerHTML = headerHtml + rowsHtml;
}


// Render Pie Chart (Category Spending) - Simple List Representation
function renderPieChart(data) {
    const chartDiv = document.getElementById("pieChart");
    
    if (!data || data.length === 0) {
        chartDiv.innerHTML = "<p>No spending data to visualize.</p>";
        return;
    }
    
    // Group by category and sum amounts (excluding Income and Savings for 'spending' chart)
    const spendingByCategory = data.reduce((acc, item) => {
        if (item.Amount > 0 && item.Category !== 'Income' && item.Category !== 'Savings') {
            acc[item.Category] = (acc[item.Category] || 0) + item.Amount;
        }
        return acc;
    }, {});
    
    const sortedCategories = Object.entries(spendingByCategory).sort(([, a], [, b]) => b - a);
    const totalExpense = sortedCategories.reduce((sum, [, amount]) => sum + amount, 0);

    if (totalExpense === 0) {
        chartDiv.innerHTML = "<p>No expenses found for this period.</p>";
        return;
    }
    
    let html = '<ul style="list-style-type: none; padding: 0; text-align: left;">';
    sortedCategories.forEach(([category, amount]) => {
        const percentage = ((amount / totalExpense) * 100).toFixed(1);
        html += `<li style="margin-bottom: 5px;">
            <strong>${category}:</strong> $${amount.toFixed(2)} (${percentage}%)
            <div style="height: 10px; background-color: #eee; border-radius: 5px; margin-top: 3px;">
                <div style="width: ${percentage}%; height: 100%; background-color: #d9534f; border-radius: 5px;"></div>
            </div>
        </li>`;
    });
    html += '</ul>';
    chartDiv.innerHTML = html;
}


// Render Weekly Graph (Weekly Spending) - Simple Bar-like Representation
function renderWeeklyGraph(data) {
    const chartDiv = document.getElementById("weeklyGraph");

    if (!data || data.length === 0) {
        chartDiv.innerHTML = "<p>No spending data to visualize.</p>";
        return;
    }
    
    // Group by week of month and sum amounts (excluding Income and Savings for 'spending' chart)
    const spendingByWeek = data.reduce((acc, item) => {
        if (item.Amount > 0 && item.Category !== 'Income' && item.Category !== 'Savings') {
            acc[item.WeekOfMonth] = (acc[item.WeekOfMonth] || 0) + item.Amount;
        }
        return acc;
    }, {});
    
    const sortedWeeks = Object.entries(spendingByWeek).sort(([a], [b]) => parseInt(a) - parseInt(b));
    const maxAmount = Math.max(...Object.values(spendingByWeek));

    if (maxAmount === 0) {
        chartDiv.innerHTML = "<p>No expenses found for this period.</p>";
        return;
    }

    let html = '<div style="display: flex; flex-direction: column; gap: 10px; padding: 10px;">';
    sortedWeeks.forEach(([week, amount]) => {
        const width = (amount / maxAmount) * 100;
        html += `<div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 60px; font-weight: bold; text-align: right;">Week ${week}:</div>
            <div style="flex-grow: 1; background-color: #f5f0f0; height: 20px; border-radius: 5px;">
                <div style="width: ${width}%; height: 100%; background-color: #5cb85c; border-radius: 5px; display: flex; align-items: center; padding-left: 5px; box-sizing: border-box;">
                    <span style="font-size: 0.8em; color: white; text-shadow: 0 0 2px black;">$${amount.toFixed(2)}</span>
                </div>
            </div>
        </div>`;
    });
    html += '</div>';
    
    chartDiv.innerHTML = html;
}


// Home button
document.getElementById("homeBtn").addEventListener("click", () => {
    localStorage.removeItem("bankData");
    window.location.href = "index.html";
});

// Manage button
document.getElementById("manageBtn").addEventListener("click", () => {
    window.location.href = "manager.html";
});

// Analyze button is not needed here as we are on analysis.html
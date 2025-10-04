const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');

// Simple CSV to Array of Objects parser
function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    const data = [];

    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        if (values.length === headers.length) {
            let obj = {};
            headers.forEach((header, index) => {
                let value = values[index];
                // Convert Amount column to number
                if (header.toLowerCase() === 'amount' && !isNaN(parseFloat(value))) {
                    obj[header] = parseFloat(value);
                } else {
                    obj[header] = value;
                }
            });
            data.push(obj);
        }
    }
    return data;
}


// Enable button only when a file is selected
fileInput.addEventListener('change', () => {
    uploadBtn.disabled = !fileInput.files.length;
});

uploadBtn.addEventListener('click', () => {
    if(fileInput.files.length > 0){
        const file = fileInput.files[0];
        const fileName = file.name.toLowerCase();

        if(file.type === "application/pdf" && fileName.includes("bank")){
            alert("PDFs not parsed yet, try CSV for charts.");
        }

        if(file.name.endsWith(".csv")) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    // PARSE CSV and save as JSON string
                    const dataArray = parseCSV(e.target.result);
                    localStorage.setItem("bankData", JSON.stringify(dataArray));
                    
                    // Redirect to analysis page
                    window.location.href = "analysis.html";
                } catch (error) {
                    alert("Error parsing CSV file.");
                }
            };
            reader.readAsText(file);
        } else {
            alert("Please upload a CSV bank statement (demo supports CSV only).");
        }
    }
});
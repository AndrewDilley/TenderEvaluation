let selectedFiles = [];  // ✅ Store selected files globally

// ✅ Handle File Selection (Prevent Overwriting)
document.getElementById("documents").addEventListener("change", function(event) {
    let files = Array.from(event.target.files);  // Convert FileList to Array

    // Append new files without replacing old ones
    files.forEach(file => {
        if (!selectedFiles.some(f => f.name === file.name)) { // Prevent duplicates
            selectedFiles.push(file);
        }
    });

    // Update UI with selected files
    let fileList = document.getElementById("selectedFilesList");
    fileList.innerHTML = "";  // Clear previous list
    selectedFiles.forEach(file => {
        fileList.innerHTML += `<li>${file.name}</li>`;
    });

    console.log("Selected files:", selectedFiles);
});

// ✅ Handle File Upload
document.getElementById("uploadForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    if (selectedFiles.length === 0) {
        alert("Please select at least one document.");
        return;
    }
    // 🚀 **FLAG: Show the loading spinner before upload starts**
    document.getElementById("loadingSpinner").classList.remove("hidden");

    let formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append("documents", file);
    });

    console.log(`Uploading ${selectedFiles.length} documents...`);

    let response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    let result;
    try {
        result = await response.json();
    } catch (error) {
        alert("Error: Invalid response from server");
        // ❌ **FLAG: Hide the spinner if an error occurs**
        document.getElementById("loadingSpinner").classList.add("hidden");
                
        return;
    }

    if (response.ok) {
        let outputDiv = document.getElementById("redactedFilesList");
        outputDiv.innerHTML = "";  // Clear previous results

        result.redacted_files.forEach(file => {
            outputDiv.innerHTML += `<li><a href="${file.redacted_text_file}" target="_blank">${file.document} (Download Redacted)</a></li>`;
        });

        document.getElementById("redactedFilesSection").classList.remove("hidden");
        document.getElementById("evaluateSection").classList.remove("hidden");

        // ✅ Clear selection after upload
        selectedFiles = [];
        document.getElementById("selectedFilesList").innerHTML = "";
    } else {
        alert("Error: " + (result.error || "Unexpected error"));
    }

    // 🚀 **FLAG: Hide the spinner after upload completes**
    document.getElementById("loadingSpinner").classList.add("hidden");

    // Reset file input field
    document.getElementById("documents").value = "";
});

// Auto-trigger evaluation when XLSX file is uploaded
document.addEventListener("DOMContentLoaded", function () {
    let evaluationInput = document.getElementById("evaluationCriteria");

    if (!evaluationInput) {
        console.error("❌ Element with ID 'evaluationCriteria' not found in the DOM.");
        return;
    }

    console.log("✅ evaluationCriteria input found. Adding event listener.");

    evaluationInput.addEventListener("change", async function () {
        let formData = new FormData();
        formData.append("evaluation_criteria", this.files[0]);

        // 🚀 **FLAG: Show spinner before evaluation starts**
        document.getElementById("loadingSpinner").classList.remove("hidden");

        console.log("Uploading XLSX for evaluation..."); // Debugging log

        let response = await fetch("/evaluate", {
            method: "POST",
            body: formData
        });

        let result;
        try {
            result = await response.json();
            console.log("✅ FULL API RESPONSE:", JSON.stringify(result, null, 2));
        } catch (error) {
            console.error("❌ Failed to parse JSON response:", error);
            alert("Error: Invalid response from server");
            // ❌ **FLAG: Hide spinner if an error occurs**
            document.getElementById("loadingSpinner").classList.add("hidden");
            return;
    
        }

        // Ensure response contains "evaluations" array
        if (!result.evaluations || !Array.isArray(result.evaluations)) {
            console.error("❌ Invalid JSON structure:", result);
            alert("Error: Invalid JSON structure");
            // ❌ **FLAG: Hide spinner if response is invalid**
            document.getElementById("loadingSpinner").classList.add("hidden");
            return;
        }

        // ✅ Insert the evaluation text for each document
        let evalOutput = document.getElementById("results");
        evalOutput.innerHTML = ""; // Clear previous content

        result.evaluations.forEach(eval => {
            evalOutput.innerHTML += `
            <div class="evaluation-card">
                <h1 style="margin-top: 0;">${eval.document.replace("_redacted.txt", "")}</h1>
                    <p>${eval.evaluation.replace(/\(Page (\d+)\)/g, '<span style="color:black;">(Page $1)</span>')}</p>
                <hr>
            </div>`;
            
        });

        // ✅ Insert the evaluation table
        if (result.evaluation_table && result.evaluation_table.trim() !== "") {
            let tableDiv = document.getElementById("evaluationTable");
            console.log("✅ Received Evaluation Table HTML:", result.evaluation_table);

            tableDiv.innerHTML = `<h3>📊 Summary Scoring Table</h3>${result.evaluation_table}`;
            tableDiv.classList.remove("hidden");
        } 

        // if (result.yes_no_table && result.yes_no_table.trim() !== "") {
        //     let yesNoTableDiv = document.getElementById("yesNoEvaluationTable");
        //     yesNoTableDiv.innerHTML = `<h3>✅ Yes/No Evaluation Table</h3>${result.yes_no_table}`;
        //     yesNoTableDiv.classList.remove("hidden");
        // }

        if (result.yes_no_table && result.yes_no_table.trim() !== "") {
            let yesNoTableDiv = document.getElementById("yesNoEvaluationTable");
            yesNoTableDiv.innerHTML = result.yes_no_table;
            yesNoTableDiv.classList.remove("hidden");
        }
        

        // Show evaluation results
        document.getElementById("evaluationResults").classList.remove("hidden");

        // ❌ **FLAG: Hide spinner if response is invalid**
        document.getElementById("loadingSpinner").classList.add("hidden");

        // hide the other sections
        document.getElementById("uploadForm").classList.add("hidden");
        document.getElementById("redactedFilesSection").classList.add("hidden");
        document.getElementById("evaluateForm").classList.add("hidden");
        
    });
});

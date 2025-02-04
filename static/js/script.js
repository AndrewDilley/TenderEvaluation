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

    // Reset file input field
    document.getElementById("documents").value = "";
});

// Auto-trigger evaluation when XLSX file is uploaded
document.getElementById("evaluationCriteria").addEventListener("change", async function () {
    let formData = new FormData();
    formData.append("evaluation_criteria", this.files[0]);

    console.log("Uploading XLSX for evaluation..."); // Debugging log

    let response = await fetch("/evaluate", {
        method: "POST",
        body: formData
    });

    let result;
    try {
        result = await response.json();
        console.log("✅ Evaluation response received:", result);
    } catch (error) {
        console.error("❌ Failed to parse JSON response:", error);
        alert("Error: Invalid response from server");
        return;
    }

    // Ensure response contains "evaluations" array
    if (!result.evaluations || !Array.isArray(result.evaluations)) {
        console.error("❌ Invalid JSON structure:", result);
        alert("Error: Invalid JSON structure");
        return;
    }

    // Update UI with evaluation results (Render as HTML)
    let evalOutput = document.getElementById("results");
//    evalOutput.innerHTML = "<h2>Evaluation Results</h2>"; // Clear previous content

    result.evaluations.forEach(eval => {
        evalOutput.innerHTML += `
        <div class="evaluation-card">
            <h1 style="margin-top: 0;">${eval.document.replace("_redacted.txt", "")}</h1>
            <p>${eval.evaluation}</p> <!-- Wrap text for better spacing -->
            <hr>
        </div>       `;
    });

    document.getElementById("evaluationResults").classList.remove("hidden");
});

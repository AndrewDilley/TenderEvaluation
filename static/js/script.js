document.getElementById("uploadForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    
    let formData = new FormData();
    let files = document.getElementById("documents").files;
    
    for (let i = 0; i < files.length; i++) {
        formData.append("documents", files[i]);
    }

    console.log("Uploading documents for redaction..."); // Debugging log
    
    let response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    let result;
    try {
        result = await response.json();
        console.log("Upload response received:", result);
    } catch (error) {
        console.error("Failed to parse JSON response:", error);
        alert("Error: Invalid response from server");
        return;
    }

    if (response.ok) {
        let outputDiv = document.getElementById("redactedFilesList");
        outputDiv.innerHTML = "";
        result.redacted_files.forEach(file => {
            outputDiv.innerHTML += `<li><a href="${file.redacted_text_file}" target="_blank">${file.document} (Download Redacted)</a></li>`;
        });

        document.getElementById("redactedFilesSection").classList.remove("hidden");
        document.getElementById("evaluateSection").classList.remove("hidden");
    } else {
        console.error("Upload error:", result);
        alert("Error: " + (result.error || "Unexpected error"));
    }
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
    evalOutput.innerHTML = "<h2>Evaluation Results</h2>"; // Clear previous content

    result.evaluations.forEach(eval => {
        evalOutput.innerHTML += `
            <div class="evaluation-card">
                <h3>${eval.document}</h3>
                <div class="evaluation-content">${eval.evaluation}</div>
                <hr>
            </div>
        `;
    });

    document.getElementById("evaluationResults").classList.remove("hidden");
});

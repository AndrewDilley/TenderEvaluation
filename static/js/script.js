$(document).ready(function () {
  $("#uploadForm").on("submit", function (event) {
      event.preventDefault();  // Stops the page from reloading

      let formData = new FormData();
      let marketDocs = $("#marketDocs")[0].files;
      let evaluationDoc = $("#evaluationDoc")[0].files[0];

      if (marketDocs.length === 0 || !evaluationDoc) {
          alert("Please upload both market response documents and evaluation criteria.");
          return;
      }

      // Append files using correct keys
      for (let i = 0; i < marketDocs.length; i++) {
          formData.append("documents", marketDocs[i]);  // Ensure correct key
      }
      formData.append("evaluation_criteria", evaluationDoc);

      // Submit via AJAX
      $.ajax({
          url: "/upload",  // Ensure endpoint matches Flask route
          type: "POST",
          data: formData,
          processData: false,
          contentType: false,
          beforeSend: function () {
              $("#evaluateButton").text("Evaluating...").prop("disabled", true);
          },
          success: function (response) {
            let formattedResults = "<h2>Evaluation Results</h2>";

            response.forEach(result => {
                formattedResults += `<h3>${result.document}</h3>`;
                formattedResults += `<p><strong>Evaluation:</strong></p><pre>${result.evaluation}</pre>`;
            });
            
            $("#results").html(formattedResults);
            $("#resultsSection").removeClass("hidden");
            
            },
          error: function (error) {
              alert("An error occurred. Check the console for details.");
              console.error(error);
          },
          complete: function () {
              $("#evaluateButton").text("Evaluate Documents").prop("disabled", false);
          },
      });
  });
});

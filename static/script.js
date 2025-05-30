async function checkScrapability() {
    let url = document.getElementById("urlInput").value;
    let statusMessage = document.getElementById("statusMessage");

    if (!url) {
        statusMessage.innerText = "Please enter a URL.";
        return;
    }

    statusMessage.innerText = "Checking scrapability...";

    try {
        let response = await fetch("/check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url })
        });

        let data = await response.json();
        statusMessage.innerText = data.message;
    } catch (error) {
        statusMessage.innerText = "Error checking scrapability.";
    }
}

async function scrapeWebsite() {
    let url = document.getElementById("urlInput").value;
    let scrapedContent = document.getElementById("scrapedContent");

    if (!url) {
        scrapedContent.innerHTML = "<p style='color:red;'>Please enter a URL.</p>";
        return;
    }

    scrapedContent.innerHTML = "<p>Scraping in progress...</p>";

    try {
        let response = await fetch("/scrape", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url })
        });

        let data = await response.json();
        scrapedContent.innerHTML = `<pre>${data.content}</pre>`;
    } catch (error) {
        scrapedContent.innerHTML = "<p style='color:red;'>Scraping failed.</p>";
    }
}

async function askQuery() {
    let query = document.getElementById("queryInput").value;
    let queryResponse = document.getElementById("queryResponse");

    if (!query) {
        queryResponse.innerHTML = "<p style='color:red;'>Please enter a query.</p>";
        return;
    }

    queryResponse.innerHTML = "<p>Processing query...</p>";

    try {
        let response = await fetch("/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
        });

        let data = await response.json();
        queryResponse.innerHTML = `<p>${data.response}</p>`;
    } catch (error) {
        queryResponse.innerHTML = "<p style='color:red;'>Query processing failed.</p>";
    }
}

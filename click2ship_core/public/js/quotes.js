// Wait until DOM is ready
document.addEventListener("DOMContentLoaded", function () {
    const quoteResponse = document.getElementById("quoteResponse");
    const loader = document.getElementById("loader");
    const quoteInput = JSON.parse(sessionStorage.getItem("quote_request"));

    if (!quoteInput) {
        quoteResponse.innerText = "No quote data found.";
        if(loader) loader.classList.add("hidden");
        return;
    }

    // Call your single combined API endpoint
    fetch("/api/method/click2ship_core.api.call.rates", {
        method: "POST",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-Frappe-CSRF-Token": csrfToken,
        },
        body: JSON.stringify(quoteInput),
        credentials: "include",
    })
    .then(res => res.json())
    .then(response => {
        const allQuotes = response.message?.Quotes || [];
        const currencyCode = response.message?.Currency || "USD";
        console.log(currencyCode);
        const currencySymbol = currencySymbols[currencyCode] || currencyCode;

        quoteResponse.innerHTML = "";

        if (allQuotes.length === 0) {
            quoteResponse.innerText = "No quotes available.";
            return;
        }

        allQuotes.sort((a, b) => a.TotalCost - b.TotalCost);

        allQuotes.forEach(q => {
            q.CurrencyCode = currencyCode;
            q.CurrencySymbol = currencySymbol;

            const quoteDiv = document.createElement("div");
            quoteDiv.classList.add("quote-wrapper");

            quoteDiv.innerHTML = `
                <div class="quote-item">
                    <div class="flex-100">
                        <img 
                            src="/assets/click2ship_core/courier_logos/${q.ServiceCode}.png"
                            alt="${q.ServiceName} Logo"
                            style="max-height: 60px;"
                            onerror="this.onerror=null; this.src='/assets/click2ship_core/courier_logos/C2S.png';"
                        />
                    </div>
                    <div class="flex-200">
                        <div class="quote-item-title">${q.ServiceName}</div>
                        ${q.Costs?.[1] ? `<div class="quote-item-desc">${q.Costs[1].Reference}</div>` : ""}
                    </div>
                    <div class="flex-100">
                        <div class="quote-item-title">${currencySymbol}${q.TotalCost.toFixed(2)}</div>
                        <div class="quote-item-desc">inclusive of VAT</div>
                    </div>
                    <div class="flex-200">
                        <div class="quote-protection-cover">
                            <div class="quote-protection-tag">
                                <span class="quote-protection-inclusive">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 48 48">
                                        <g fill="none" stroke="currentColor" stroke-linejoin="round" stroke-width="4">
                                            <path d="M6 9.256L24.009 4L42 9.256v10.778A26.316 26.316 0 0 1 24.003 45A26.32 26.32 0 0 1 6 20.029z"></path>
                                            <path stroke-linecap="round" d="m15 23l7 7l12-12"></path>
                                        </g>
                                    </svg>
                                    <span>Inc <strong>${currencySymbol}${q.Costs?.[2]?.TotalCost || ""}</strong> Protection</span>
                                </span>
                                <span class="quote-protection-upgrade">Standard Insurance</span>
                            </div>
                        </div>
                    </div>
                    <div class="flex-150">
                        <div class="quote-item-desc text-red">
                            Delivery expected by<br/>${q.PrettyTransitTime || "N/A"} (${q.TransitTime || "N/A"})
                        </div>
                    </div>
                    <div class="flex-100">
                        <button type="button" class="nav-btn -outlined book-now-btn" data-quote='${JSON.stringify(q)}'>Book Now</button>
                    </div>
                </div>
            `;

            quoteResponse.appendChild(quoteDiv);
        });
    })
    .catch(err => {
        console.error("Fetch error:", err);
        quoteResponse.innerText = "Error fetching shipping quotes.";
    })
    .finally(() => {
        if(loader) loader.classList.add("hidden");
    });

    // Handle Book Now
    quoteResponse.addEventListener("click", function (e) {
        const btn = e.target.closest(".book-now-btn");
        if (btn) {
            e.preventDefault();
            try {
                const quote = JSON.parse(btn.dataset.quote);
                bookNow(quote);
            } catch (err) {
                console.error("Invalid quote data", err);
            }
        }
    });

    function bookNow(quote) {
        fetch("/api/method/click2ship_core.api.call.session_save", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Frappe-CSRF-Token": csrfToken,
            },
            body: JSON.stringify({ quote }),
            credentials: "include",
        })
            .then(res => res.json())
            .then(r => {
                if (r.message && r.message.status === "success") {
                    window.location.href = "/booking";
                } else {
                    alert("Failed to save quote");
                }
            })
            .catch(err => {
                console.error("Error saving quote:", err);
                alert("An error occurred while saving the quote");
            });
    }
});

document.addEventListener("submit", function (event) {
    var form = event.target.closest("[data-reaction-form]");
    if (!form) {
        return;
    }
    event.preventDefault();
    var body = new FormData(form);
    if (event.submitter && event.submitter.name) {
        body.set(event.submitter.name, event.submitter.value);
    }
    form.classList.add("is-busy");
    fetch(form.action, {
        method: "POST",
        body: body,
        credentials: "same-origin",
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
        .then(function (response) {
            if (!response.ok) {
                throw new Error("request failed");
            }
            return response.json();
        })
        .then(function (data) {
            form.querySelectorAll("[data-kind]").forEach(function (button) {
                var kind = button.getAttribute("data-kind");
                var counter = button.querySelector("[data-count]");
                var active = data.mine === kind;
                if (counter) {
                    counter.textContent = data.counts[kind];
                }
                button.classList.toggle("is-active", active);
                button.setAttribute("aria-pressed", active ? "true" : "false");
            });
        })
        .catch(function () {
            window.location.reload();
        })
        .finally(function () {
            form.classList.remove("is-busy");
        });
});
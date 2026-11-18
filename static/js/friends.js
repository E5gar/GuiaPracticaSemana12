document.addEventListener("DOMContentLoaded", function () {
    var input = document.querySelector("[data-friend-filter]");
    if (!input) {
        return;
    }
    var items = document.querySelectorAll("[data-filter-item]");
    input.addEventListener("input", function () {
        var term = input.value.trim().toLowerCase();
        items.forEach(function (item) {
            var name = item.getAttribute("data-name") || "";
            item.hidden = term !== "" && name.indexOf(term) === -1;
        });
    });
});
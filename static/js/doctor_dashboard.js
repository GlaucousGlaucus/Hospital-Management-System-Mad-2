document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll("input[name='availability']").forEach(function(cb) {
        cb.addEventListener("change", function() {
            const data = {
                slot: cb.value,
                enabled: cb.checked ? 1 : 0
            };

            fetch(UPDATE_AVAILABILITY_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data)
            }).catch(error => { alert("Error updating availability"); console.error(error); });
        });
    });
});

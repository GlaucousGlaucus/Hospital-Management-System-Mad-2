const SLOT_TIMES = {
    morning: "08:00",
    evening: "16:00"
}

let selectedSlot = null;
let selectedData = null;
let dialog_context = {
        type: 'booking',
        data: {}
    };

function openAvailabilityModal(doctorId, context) {
    dialog_context = {
        type: context.type || 'booking',
        data: context.data || {}
    };
    fetch(`/api/doctor/${doctorId}/availability_json`)
        .then(resp => resp.json())
        .then(data => buildAvailabilityGrid(data));

    document.getElementById("availabilityModal").style.display = "flex";
}

function closeAvailabilityModal() {
    document.getElementById("availabilityModal").style.display = "none";
    document.getElementById("availabilityGrid").innerHTML = "";
    selectedSlot = null;
    selectedData = null;
    document.getElementById("bookBtn").disabled = true;
}

function buildAvailabilityGrid(data) {
    const grid = document.getElementById("availabilityGrid");
    grid.innerHTML = "";

    data.forEach(day => {
        const row = document.createElement("div");
        row.className = "av-row";

        const dateBox = document.createElement("div");
        dateBox.className = "av-date";
        dateBox.innerText = day.date_display;
        row.appendChild(dateBox);

        ["morning", "evening"].forEach(slot => {
            const slotBox = document.createElement("div");
            const available = day[slot].available;
            const label = day[slot].label;

            slotBox.className = "av-slot " + (available ? "av-available" : "av-unavailable");
            slotBox.innerText = label;

            slotBox.onclick = () => {
                if (!available) return;

                document.querySelectorAll(".av-slot").forEach(e =>
                    e.classList.remove("av-selected")
                );

                slotBox.classList.add("av-selected");
                selectedSlot = slot;
                selectedData = day;
                document.getElementById("bookBtn").disabled = false;
            };

            row.appendChild(slotBox);
        });

        grid.appendChild(row);
    });

    document.getElementById("bookBtn").onclick = () => emitSelection();
}

function emitSelection() {
    if (!selectedData || !selectedSlot) return;

    const event = new CustomEvent("availability:selected", {
        detail: {
            doctor_id: selectedData.doctor_id,
            date: selectedData.date,
            slot: selectedSlot,
            time: SLOT_TIMES[selectedSlot],
            type: dialog_context.type,
            extra_data: dialog_context.data
        }
    });

    document.dispatchEvent(event);
    closeAvailabilityModal();
}

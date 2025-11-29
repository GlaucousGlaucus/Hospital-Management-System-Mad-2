const SLOT_KEYS = ["morning", "afternoon", "evening"];

const SLOT_TIME_MAP = {
    morning: "08:00",
    afternoon: "12:00",
    evening: "16:00"
};

let selectedSlot = null;
let selectedData = null;
let dialog_context = {
    type: "booking",
    data: {}
};

function openAvailabilityModal(doctorId, context) {
    dialog_context = {
        type: context?.type || "booking",
        data: context?.data || {}
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

        SLOT_KEYS.forEach(slot => {
            const slotInfo = day[slot];
            console.log(slotInfo, slot);
            const slotBox = document.createElement("div");
            slotBox.className =
                "av-slot " + (slotInfo.available ? "av-available" : "av-unavailable");
            slotBox.innerText = slotInfo.label;

            slotBox.onclick = () => {
                if (!slotInfo.available) return;

                document.querySelectorAll(".av-slot").forEach(e =>
                    e.classList.remove("av-selected")
                );

                slotBox.classList.add("av-selected");
                selectedSlot = slot;

                selectedData = {
                    doctor_id: day.doctor_id,
                    date: day.date,
                    slot: slot,
                    start_time: SLOT_TIME_MAP[slot],
                    end_time: null
                };

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
            time: selectedData.start_time, // API expects "time"
            slot: selectedData.slot,
            start_time: selectedData.start_time,
            type: dialog_context.type,
            extra_data: dialog_context.data
        }
    });

    document.dispatchEvent(event);
    closeAvailabilityModal();
}

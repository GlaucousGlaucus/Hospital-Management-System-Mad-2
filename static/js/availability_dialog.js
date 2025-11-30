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
        .then(data => buildAvailabilityGrid(data, dialog_context.type));

    if (dialog_context.type === "edit") {
        document.getElementById("bookBtn").style.display = "none";
    }
    document.getElementById("availabilityModal").style.display = "flex";
}

function closeAvailabilityModal() {
    document.getElementById("availabilityModal").style.display = "none";
    document.getElementById("availabilityGrid").innerHTML = "";
    selectedSlot = null;
    selectedData = null;
    document.getElementById("bookBtn").disabled = true;
}

function buildAvailabilityGrid(data, mode = "booking") {
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
            const slotBox = document.createElement("div");
            slotBox.className =
                "av-slot " + (slotInfo.available ? "av-available" : "av-unavailable");
            slotBox.innerText = slotInfo.label;

            slotBox.onclick = () => {
                if (mode === "booking" || mode === "reschedule") {
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
                }

                else if (mode === "edit") {
                    slotInfo.available = !slotInfo.available;

                    slotBox.classList.toggle("av-available", slotInfo.available);
                    slotBox.classList.toggle("av-unavailable", !slotInfo.available);

                    const slotKey = `${day.date}_${slot}`;

                    fetch(UPDATE_AVAILABILITY_URL, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            slot: slotKey,
                            enabled: slotInfo.available
                        })
                    })
                        .then(resp => resp.json())
                        .then(res => {

                            if (res.status === "success") {
                                slotBox.classList.add("av-saved");
                                setTimeout(() => slotBox.classList.remove("av-saved"), 400);
                            } else {
                                alert("Error updating availability");
                                console.log(res);
                            }
                        })
                        .catch(() => {
                            alert("Network error");

                            slotInfo.available = !slotInfo.available;
                            slotBox.classList.toggle("av-available", slotInfo.available);
                            slotBox.classList.toggle("av-unavailable", !slotInfo.available);
                        });
                }
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

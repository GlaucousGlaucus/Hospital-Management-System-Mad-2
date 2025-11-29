import {createAppointmentRow, createPersonListCard} from "./components/person_list_cards.js";

document.addEventListener("DOMContentLoaded", () => {
    loadDoctors().then(r => {});
    loadPatients().then(r => {});
    loadAppointments().then(r => {});

    const collapsibles = document.querySelectorAll(".collapsible");

    collapsibles.forEach(c => {
        c.addEventListener("click", () => {
            c.classList.toggle("active");
            const content = c.nextElementSibling;
            content.classList.toggle("open");
        });
    });

    document.body.addEventListener("click", async (event) => {
        const btn = event.target.closest("[data-action]");
        if (!btn) return;

        const { action, type, id } = btn.dataset;
        console.log(`Action: ${action}, Type: ${type}, ID: ${id}`);

        if (action === "delete") {
            if (!confirm(`Delete this ${type}?`)) return;
            const res = await fetch(`/api/${type}/${id}`, { method: "DELETE" });
            const data = await res.json();
            if (data.status === "deleted") {
                switch (type) {
                    case "doctor":
                        loadDoctors().then(r => {});
                        break
                    case "patient":
                        loadPatients().then(r => {});
                        break
                    case "appointment":
                        loadAppointments().then(r => {});
                        break
                }
            } else {
                alert(data.error || "Failed to delete");
            }
        }
        else if (action === "edit") {
            window.location.href = `/admin/edit/${type}/${id}`;
        }
        else if (action === "blacklist") {
            const res = await fetch(`/api/${type}/${id}/blacklist`, { method: "PATCH" });
            const data = await res.json();
            if (data.status === "updated") alert("User blacklisted!");
        }
    });
});

async function loadDoctors() {
    const container = document.getElementById("doctor-list");
    const header = document.getElementById("doctor-header");

    container.innerHTML = "<p>Loading...</p>";

    const res = await fetch("/api/doctors/all", { method: "GET" });
    const data = await res.json();

    header.innerText = `Doctors (${data?.length | 0})`;

    if (!data || !data.length) {
        container.innerHTML = "<p class='empty-text'>No doctors registered.</p>";
        return;
    }

    container.innerHTML = data.map(d => createPersonListCard(d, "doctor")).join("");
}

async function loadPatients() {
    const container = document.getElementById("patient-list");
    const header = document.getElementById("patient-header");

    container.innerHTML = "<p>Loading...</p>";
    const res = await fetch("/api/patients/all", { method: "GET" });
    const data = await res.json();

    header.innerText = `Patients (${data?.length | 0})`;

    if (!data || !data.length) {
        container.innerHTML = "<p class='empty-text'>No patients registered.</p>";
        return;
    }

    container.innerHTML = data.map(d => createPersonListCard(d, "patient")).join("");
}

async function loadAppointments() {
    const container = document.getElementById("appointments-table");
    const header = document.getElementById("upcoming-appt-header");

    container.innerHTML = "<tr><td colSpan=\"5\" className=\"empty-text\">No upcoming appointments.</td></tr>";

    const res = await fetch("/api/appointments/all", {method: "GET"});
    const data = await res.json();

    header.innerText = `${data?.length | 0} Upcoming Appointments`;

    if (!data || !data.length) {
        container.innerHTML = "<tr><td colSpan=\"5\" className=\"empty-text\">No upcoming appointments.</td></tr>";
        return;
    }

    container.innerHTML = data.map(d => createAppointmentRow(d)).join("");
}

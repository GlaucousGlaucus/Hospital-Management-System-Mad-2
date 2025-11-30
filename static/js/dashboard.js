import {createAppointmentRow, createPersonListCard} from "./components/person_list_cards.js";

document.addEventListener("DOMContentLoaded", () => {
    loadDoctors();
    loadPatients();
    loadAppointments();
    loadPastAppointments();

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
            const res = await fetch(`/api/blacklist/${type}/${id}`, { method: "POST" });
            const data = await res.json();
            if (data.status === "blacklisted") {
                alert("User blacklisted!");
                if (type === "doctor") loadDoctors();
                if (type === "patient") loadPatients();
            }
        }
        else if (action === "unblacklist") {
            const res = await fetch(`/api/unblacklist/${type}/${id}`, { method: "POST" });
            const data = await res.json();
            if (data.status === "unblacklisted") {
                alert("User removed from blacklist!");
                if (type === "doctor") loadDoctors();
                if (type === "patient") loadPatients();
            }
        }
        else if (action === "reschedule") {
            openAvailabilityModal(btn.dataset.doctor, {
                type: "reschedule",
                data: { appointment_id: id }
            });
        }
        else if (action === "complete") {
            await fetch(`/api/doctor/appointment/${id}/complete`, { method: "POST" });
            loadAppointments();
            loadPastAppointments();
        }
        else if (action === "cancel") {
            await fetch(`/api/appointment/${id}/cancel`, { method: "POST" });
            loadAppointments();
            loadPastAppointments();
        }
    });
});

async function loadDoctors(list = null) {
    const container = document.getElementById("doctor-list");
    const header = document.getElementById("doctor-header");

    container.innerHTML = "<p>Loading...</p>";

    let data = list;

    if (!data) {
        const res = await fetch("/api/doctors/all");
        data = await res.json();
    }

    header.innerText = `Doctors (${data.length || 0})`;

    if (!data.length) {
        container.innerHTML = "<p class='empty-text'>No doctors found.</p>";
        return;
    }

    container.innerHTML = data.map(d => createPersonListCard(d, "doctor")).join("");
}

async function loadPatients(list = null) {
    const container = document.getElementById("patient-list");
    const header = document.getElementById("patient-header");

    container.innerHTML = "<p>Loading...</p>";

    let data = list;

    if (!data) {
        const res = await fetch("/api/patients/all");
        data = await res.json();
    }

    header.innerText = `Patients (${data.length || 0})`;

    if (!data.length) {
        container.innerHTML = "<p class='empty-text'>No patients found.</p>";
        return;
    }

    container.innerHTML = data.map(d => createPersonListCard(d, "patient")).join("");
}

async function loadAppointments(list = null) {
    const container = document.getElementById("appointments-table");
    const header = document.getElementById("upcoming-appt-header");

    container.innerHTML = "<tr><td colspan='5'>Loading...</td></tr>";

    let data = list;

    if (!data) {
        const res = await fetch("/api/appointments/upcoming");
        data = await res.json();
    }

    header.innerText = `${data.length || 0} Upcoming Appointments`;

    if (!data.length) {
        container.innerHTML = "<tr><td colspan='5' class='empty-text'>No appointments found.</td></tr>";
        return;
    }

    container.innerHTML = data.map(d => createAppointmentRow(d)).join("");
}


async function loadPastAppointments(list = null) {
    const container = document.getElementById("past-appointments-table");
    const header = document.getElementById("past-appt-header");

    container.innerHTML = "<tr><td colspan='5' class='empty-text'>Loading...</td></tr>";

    let data = list;
    if (!data) {
        const res = await fetch("/api/appointments/past", { method: "GET" });
        data = await res.json();
    }

    header.innerText = `${data.length || 0} Past Appointments`;

    if (!data.length) {
        container.innerHTML = "<tr><td colspan='5' class='empty-text'>No past appointments.</td></tr>";
        return;
    }

    container.innerHTML = data.map(d => createAppointmentRow(d, true)).join("");
}

async function performSearch() {
    const q = document.querySelector(".dashboard-search").value.trim();

    if (!q) {
        loadDoctors();
        loadPatients();
        loadAppointments();
        loadPastAppointments();
        return;
    }

    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();

    const upcoming = data.appointments.filter(a => a.is_upcoming);
    const past = data.appointments.filter(a => !a.is_upcoming);

    loadDoctors(data.doctors);
    loadPatients(data.patients);
    loadAppointments(upcoming);
    loadPastAppointments(past);
}


const searchInput = document.querySelector(".dashboard-search");
const searchButton = document.querySelector(".btn.btn-filled");

searchButton.addEventListener("click", performSearch);
searchInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") performSearch();
});

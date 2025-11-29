document.addEventListener("availability:selected", async function(e) {
    const data = e.detail;
    if (!data || !data.type) return;

    switch (data.type) {
        case "booking":
            await bookAppointment(data);
            break;

        case "reschedule":
            await rescheduleAppointment(data.extra_data.appointment_id, data);
            break;
    }
});

async function bookAppointment(data) {
    const resp = await fetch("/api/book_appointment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            doctor_id: data.doctor_id,
            date: data.date,
            time: data.time,
            visit_type: "Checkup"
        })
    });

    const result = await resp.json();

    if (result.error) {
        alert(result.error);
    } else {
        alert("Appointment booked!");
        location.reload();
    }
}

async function rescheduleAppointment(appointmentId, data) {
    const resp = await fetch(`/api/appointment/${appointmentId}/reschedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            new_date: data.date,
            new_time: data.time
        })
    });

    const result = await resp.json();

    if (result.error) {
        alert(result.error);
    } else {
        alert("Appointment rescheduled!");
        location.reload();
    }
}

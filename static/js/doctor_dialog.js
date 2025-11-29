let currentDoctor = null;

function openDoctorModal(doctor) {
    currentDoctor = doctor;

    document.getElementById("doctorName").innerText = "Dr. " + doctor.name;
    document.getElementById("doctorSpecialization").innerText = doctor.specialization || "N/A";
    document.getElementById("doctorAge").innerText = doctor.age || "N/A";
    document.getElementById("doctorContact").innerText = doctor.contact || "N/A";

    document.getElementById("doctorModal").style.display = "flex";
}

function closeDoctorModal() {
    document.getElementById("doctorModal").style.display = "none";
}

document.addEventListener("click", function (e) {
    if (e.target.classList.contains("doctor-view-btn")) {
        const doctor = JSON.parse(e.target.dataset.doctor);
        openDoctorModal(doctor);
    }
});

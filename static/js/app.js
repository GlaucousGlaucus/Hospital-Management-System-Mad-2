const { createApp } = Vue;

const required = (type) => ({ type, required: true });
const component = (template, props) => ({ template, props });
const emptySignupForm = () => ({ name: "", email: "", password: "", dob: "", contact: "" });
const emptyPatientSearch = () => ({ q: "", department: "", date: "", slot: "", results: [] });
const emptyTreatmentForm = () => ({
    appointment: null,
    visit_type: "",
    test_done: "",
    diagnosis: "",
    prescription: "",
    notes: "",
    medicines: [],
});
const emptyMedicineRow = () => ({
    name: "",
    morning: 0,
    afternoon: 0,
    night: 0,
    duration_days: 1,
    instructions: "",
});
const createUserForm = (extra = {}) => ({
    id: null,
    name: "",
    email: "",
    password: "",
    dob: "",
    contact: "",
    ...extra,
});
const createFormMeta = (entity) => ({
    title: entity.id ? `Edit ${entity.label}` : `Create ${entity.label}`,
    submitLabel: entity.id ? `Update ${entity.label}` : `Create ${entity.label}`,
});
const createAvailabilityModal = (overrides = {}) => ({
    open: false,
    doctorId: null,
    action: "book",
    appointmentId: null,
    schedule: [],
    selectedDate: "",
    selectedSlot: "",
    visitType: "Checkup",
    ...overrides,
});
const statusClassMap = {
    Completed: "status-pill-success",
    Failed: "status-pill-danger",
    Processing: "status-pill-primary",
    SUCCESS: "status-pill-success",
    FAILURE: "status-pill-danger",
    STARTED: "status-pill-primary",
    PROGRESS: "status-pill-primary",
};
const slotTimeMap = {
    morning: "09:00",
    afternoon: "13:00",
    evening: "17:00",
};
const batchTaskConfig = {
    "daily-summary": {
        summary: (result) => [
            { label: "Doctors", value: result.totals?.doctors ?? 0 },
            { label: "Patients", value: result.totals?.patients ?? 0 },
            { label: "Appointments Today", value: result.totals?.appointments_today ?? 0 },
            { label: "Booked", value: result.statuses?.booked ?? 0 },
            { label: "Completed", value: result.statuses?.completed ?? 0 },
            { label: "Cancelled", value: result.statuses?.cancelled ?? 0 },
        ],
    },
    "daily-reminders": {
        summary: (result) => [
            { label: "Date", value: result.date || "N/A" },
            { label: "Appointments Considered", value: result.appointments_considered ?? 0 },
            { label: "Notifications Sent", value: result.notifications_sent ?? 0 },
        ],
        rows: (result) => result.reminders || [],
        rowKey: (row, index) => row.appointment_id || index,
    },
    "monthly-activity": {
        summary: (result) => [
            { label: "Period Start", value: result.period_start || "N/A" },
            { label: "Period End", value: result.period_end || "N/A" },
            { label: "Reports Generated", value: result.reports_generated ?? 0 },
            { label: "Reports Delivered", value: result.reports_delivered ?? 0 },
        ],
        rows: (result) => result.items || [],
        rowKey: (row, index) => row.doctor_id || index,
    },
};
const adminSearchFields = {
    doctors: (doctor) => [
        doctor.name,
        doctor.email,
        doctor.contact,
        doctor.specialization,
        doctor.department_name,
        doctor.is_blacklisted ? "blacklisted" : "active",
    ],
    patients: (patient) => [
        patient.name,
        patient.email,
        patient.contact,
        patient.is_blacklisted ? "blacklisted" : "active",
    ],
    appointments: (appointment) => [
        appointment.patient?.name,
        appointment.patient?.email,
        appointment.doctor?.name,
        appointment.doctor?.email,
        appointment.doctor?.specialization,
        appointment.doctor?.department_name,
        appointment.visit_type,
        appointment.status,
        appointment.date,
        appointment.time,
    ],
};
const routePatterns = [
    { regex: /^\/login$/, name: "home", authMode: "login" },
    { regex: /^\/signup$/, name: "home", authMode: "signup" },
    { regex: /^\/dashboard$/, name: "dashboard" },
    { regex: /^\/admin\/new\/doctor$/, name: "doctorForm" },
    { regex: /^\/admin\/edit\/doctor\/(\d+)$/, name: "doctorForm", params: ["id"] },
    { regex: /^\/admin\/new\/patient$/, name: "patientForm" },
    { regex: /^\/admin\/edit\/patient\/(\d+)$/, name: "patientForm", params: ["id"] },
    { regex: /^\/doctor\/update_history\/(\d+)$/, name: "treatmentForm", params: ["appointmentId"] },
    { regex: /^\/doctor\/edit$/, name: "profileForm" },
    { regex: /^\/patient\/edit\/profile$/, name: "profileForm" },
    { regex: /^\/patient\/department\/(\d+)$/, name: "department", params: ["departmentId"] },
    { regex: /^\/history\/patient\/(\d+)$/, name: "history", params: ["patientId"] },
];
const AppAlerts = component("#app-alerts-template", {
    alerts: required(Array),
    dismissAlert: required(Function),
});
const AppNavbar = component("#app-navbar-template", {
    appContext: required(Object),
    goHome: required(Function),
    navigate: required(Function),
    logout: required(Function),
});
const PublicHome = component("#public-home-template", {
    authMode: required(String),
    authForm: required(Object),
    signupForm: required(Object),
    setAuthMode: required(Function),
    submitLogin: required(Function),
    submitSignup: required(Function),
});
const WorkspaceHeader = component("#workspace-header-template", {
    user: required(Object),
    viewTitle: required(String),
    viewSubtitle: required(String),
});
const AdminDashboard = component("#admin-dashboard-template", {
    dashboard: required(Object),
    adminSearch: required(Object),
    filteredAdminDoctors: required(Array),
    filteredAdminPatients: required(Array),
    filteredAdminAppointments: required(Array),
    filteredAdminPastAppointments: required(Array),
    batchTask: { type: Object, default: null },
    runAdminSearch: required(Function),
    navigate: required(Function),
    startBatchReport: required(Function),
    startDailyReminders: required(Function),
    startMonthlyActivityReport: required(Function),
    batchTaskStateClass: required(Function),
    batchTaskSummary: required(Function),
    batchTaskRows: required(Function),
    batchTaskRowKey: required(Function),
    toggleBlacklist: required(Function),
    deleteEntity: required(Function),
    openPatientHistory: required(Function),
    openAvailabilityModal: required(Function),
    markComplete: required(Function),
    cancelAppointment: required(Function),
    formatDate: required(Function),
    formatTime: required(Function),
});
const DoctorDashboard = component("#doctor-dashboard-template", {
    dashboard: required(Object),
    navigate: required(Function),
    formatDate: required(Function),
    formatTime: required(Function),
    openPatientHistory: required(Function),
    openAvailabilityModal: required(Function),
    markComplete: required(Function),
    cancelAppointment: required(Function),
    doctorAvailabilityButtonClass: required(Function),
    toggleAvailability: required(Function),
});
const PatientDashboard = component("#patient-dashboard-template", {
    dashboard: required(Object),
    departments: required(Array),
    patientSearch: required(Object),
    exportJobs: required(Array),
    navigate: required(Function),
    openPatientHistory: required(Function),
    startTreatmentExport: required(Function),
    loadExports: required(Function),
    formatDate: required(Function),
    formatTime: required(Function),
    formatDateTime: required(Function),
    exportStatusClass: required(Function),
    runPatientSearch: required(Function),
    resetPatientSearch: required(Function),
    openAvailabilityModal: required(Function),
    cancelAppointment: required(Function),
});
const DepartmentDetails = component("#department-details-template", {
    selectedDepartment: required(Object),
    navigate: required(Function),
    openAvailabilityModal: required(Function),
});
const PatientHistory = component("#patient-history-template", {
    patientHistory: required(Object),
    exportJobs: required(Array),
    navigate: required(Function),
    startTreatmentExport: required(Function),
    canQueueTreatmentExport: required(Function),
    loadExports: required(Function),
    historyPatientId: required(Function),
    formatDate: required(Function),
    formatDateTime: required(Function),
    exportStatusClass: required(Function),
});
const UserForm = component("#user-form-template", {
    activeForm: required(Object),
    formMeta: required(Object),
    departments: required(Array),
    showDoctorFields: required(Boolean),
    routeName: required(String),
    navigate: required(Function),
    submitActiveForm: required(Function),
});
const TreatmentForm = component("#treatment-form-template", {
    treatmentForm: required(Object),
    navigate: required(Function),
    submitTreatmentForm: required(Function),
    addMedicineRow: required(Function),
    removeMedicineRow: required(Function),
});
const AvailabilityModal = component("#availability-modal-template", {
    availabilityModal: required(Object),
    closeAvailabilityModal: required(Function),
    availabilityButtonClass: required(Function),
    selectAvailability: required(Function),
    confirmAvailabilityAction: required(Function),
});

const app = createApp({
    delimiters: ["[[", "]]"],
    components: {
        AppAlerts,
        AppNavbar,
        PublicHome,
        WorkspaceHeader,
        AdminDashboard,
        DoctorDashboard,
        PatientDashboard,
        DepartmentDetails,
        PatientHistory,
        UserForm,
        TreatmentForm,
        AvailabilityModal,
    },
    data() {
        return {
            loading: true,
            appContext: {
                user: null,
                departments: [],
            },
            dashboard: null,
            route: { name: "home", params: {} },
            alerts: [],
            authMode: "login",
            authForm: {
                email: "",
                password: "",
                user_type: "patient",
            },
            signupForm: emptySignupForm(),
            adminSearch: {
                q: "",
                appliedQuery: "",
            },
            patientSearch: emptyPatientSearch(),
            activeForm: null,
            formMeta: {
                title: "",
                submitLabel: "",
            },
            selectedDepartment: null,
            patientHistory: null,
            treatmentForm: emptyTreatmentForm(),
            availabilityModal: createAvailabilityModal(),
            batchTask: null,
            pollHandle: null,
            exportJobs: [],
            exportPollHandle: null,
            emptyTreatmentForm,
        };
    },
    computed: {
        viewTitle() {
            switch (this.route.name) {
                case "dashboard":
                    return "Dashboard";
                case "department":
                    return "Department Details";
                case "history":
                    return "Patient History";
                case "doctorForm":
                    return this.route.params.id ? "Edit Doctor" : "Create Doctor";
                case "patientForm":
                    return this.route.params.id ? "Edit Patient" : "Create Patient";
                case "profileForm":
                    return "Edit Profile";
                case "treatmentForm":
                    return "Update Treatment";
                default:
                    return "Workspace";
            }
        },
        viewSubtitle() {
            if (!this.appContext.user) {
                return "Single page hospital operations.";
            }
            const role = this.appContext.user.user_type;
            if (this.route.name === "dashboard") {
                if (role === "admin") return "Manage doctors, patients, appointments, and batch jobs.";
                if (role === "doctor") return "Track appointments, update treatment records, and maintain availability.";
                return "Book appointments, review departments, and manage your profile.";
            }
            return "";
        },
        showDoctorFields() {
            return this.route.name === "doctorForm"
                || (this.route.name === "profileForm" && this.appContext.user?.user_type === "doctor");
        },
        adminSearchTerm() {
            return (this.adminSearch.appliedQuery || "").trim().toLowerCase();
        },
        filteredAdminDoctors() {
            return this.filterAdminCollection(this.dashboard?.doctors, adminSearchFields.doctors);
        },
        filteredAdminPatients() {
            return this.filterAdminCollection(this.dashboard?.patients, adminSearchFields.patients);
        },
        filteredAdminAppointments() {
            return this.filterAdminCollection(this.dashboard?.upcoming_appointments, adminSearchFields.appointments);
        },
        filteredAdminPastAppointments() {
            return this.filterAdminCollection(this.dashboard?.past_appointments, adminSearchFields.appointments);
        },
    },
    mounted() {
        window.addEventListener("popstate", this.handlePopState);
        this.initializeAppContext();
    },
    beforeUnmount() {
        window.removeEventListener("popstate", this.handlePopState);
        if (this.pollHandle) {
            clearTimeout(this.pollHandle);
        }
        if (this.exportPollHandle) {
            clearTimeout(this.exportPollHandle);
        }
    },
    methods: {
        async api(url, options = {}) {
            const fetchOptions = {
                method: options.method || "GET",
                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {}),
                },
                credentials: "same-origin",
            };
            if (options.body !== undefined) {
                fetchOptions.body = JSON.stringify(options.body);
            }
            const response = await fetch(url, fetchOptions);
            const text = await response.text();
            let payload = {};
            if (text) {
                try {
                    payload = JSON.parse(text);
                } catch {
                    payload = { raw: text };
                }
            }
            if (!response.ok) {
                throw new Error(payload.error || payload.message || "Request failed.");
            }
            return payload;
        },
        pushAlert(message, variant = "success") {
            const id = Date.now() + Math.random();
            this.alerts.unshift({ id, message, variant });
            setTimeout(() => this.dismissAlert(id), 5000);
        },
        dismissAlert(id) {
            this.alerts = this.alerts.filter((alert) => alert.id !== id);
        },
        matchesAdminSearch(_, fields) {
            return fields.some((field) => String(field || "").toLowerCase().includes(this.adminSearchTerm));
        },
        filterAdminCollection(collection = [], getFields) {
            if (!this.adminSearchTerm) return collection || [];
            return (collection || []).filter((item) => this.matchesAdminSearch(item, getFields(item)));
        },
        handleError(error) {
            this.pushAlert(error.message || "Unexpected error.", "danger");
        },
        async attempt(action) {
            try {
                return await action();
            } catch (error) {
                this.handleError(error);
                return null;
            }
        },
        setAuthMode(mode) {
            this.authMode = mode;
            this.navigate(mode === "signup" ? "/signup/" : "/login/");
        },
        resolveRoute(pathname) {
            const clean = pathname.length > 1 ? pathname.replace(/\/$/, "") : pathname;
            for (const pattern of routePatterns) {
                const match = clean.match(pattern.regex);
                if (!match) continue;
                const params = {};
                (pattern.params || []).forEach((key, index) => {
                    params[key] = match[index + 1];
                });
                if (pattern.authMode) {
                    this.authMode = pattern.authMode;
                }
                return { name: pattern.name, params };
            }

            return { name: this.appContext.user ? "dashboard" : "home", params: {} };
        },
        navigate(path, pushState = true) {
            if (pushState) {
                window.history.pushState({}, "", path);
            }
            this.route = this.resolveRoute(path);
            this.loadRouteData();
        },
        goHome() {
            this.navigate(this.appContext.user ? "/dashboard/" : "/");
        },
        handlePopState() {
            this.route = this.resolveRoute(window.location.pathname);
            this.loadRouteData();
        },
        formatDate(value) {
            if (!value) return "";
            return new Date(`${value}T00:00:00`).toLocaleDateString();
        },
        formatTime(value) {
            if (!value) return "";
            const normalized = value.length === 5 ? `${value}:00` : value;
            return new Date(`1970-01-01T${normalized}`).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        },
        formatDateTime(value) {
            if (!value) return "";
            return new Date(value).toLocaleString();
        },
        timeForSlot(slot) {
            return slotTimeMap[slot] || slotTimeMap.evening;
        },
        historyPatientId() {
            return this.patientHistory?.patient?.id || null;
        },
        currentExportPatientId() {
            if (this.route.name === "history") return this.historyPatientId();
            return this.appContext.user?.user_type === "patient" ? this.appContext.user.id : null;
        },
        canQueueTreatmentExport() {
            return Boolean(this.currentExportPatientId());
        },
        exportStatusClass(status) {
            return statusClassMap[status] || "status-pill-secondary";
        },
        batchTaskStateClass(state) {
            return statusClassMap[state] || "status-pill-secondary";
        },
        batchTaskSummary(task) {
            return batchTaskConfig[task?.kind]?.summary?.(task?.result) || [];
        },
        batchTaskRows(task) {
            return batchTaskConfig[task?.kind]?.rows?.(task?.result) || [];
        },
        batchTaskRowKey(task, taskRow, index) {
            return batchTaskConfig[task?.kind]?.rowKey?.(taskRow, index) || index;
        },
        async queueBatchTask(url, kind, label, queuedMessage) {
            const payload = await this.api(url, { method: "POST" });
            this.batchTask = {
                task_id: payload.task_id,
                state: payload.status,
                kind,
                label,
            };
            this.pushAlert(queuedMessage, "info");
            this.pollBatchTask(payload.task_id);
        },
        resetTransientState() {
            this.activeForm = null;
            this.formMeta = { title: "", submitLabel: "" };
            this.selectedDepartment = null;
            this.patientHistory = null;
            this.treatmentForm = this.emptyTreatmentForm();
        },
        async initializeAppContext() {
            this.loading = true;
            await this.attempt(async () => {
                const data = await this.api("/api/app-context");
                this.appContext = data;
                this.route = this.resolveRoute(window.location.pathname);
                await this.loadRouteData();
            });
            this.loading = false;
        },
        async loadDashboard() {
            this.dashboard = await this.api("/api/dashboard");
            if (this.appContext.user?.user_type === "patient") {
                this.exportJobs = this.dashboard.export_jobs || [];
            }
        },
        async loadRouteData() {
            this.resetTransientState();
            if (!this.appContext.user) return;

            const loaders = {
                dashboard: async () => {
                    await this.loadDashboard();
                    if (this.appContext.user.user_type === "patient" && !this.patientSearch.results.length) {
                        await this.runPatientSearch();
                    }
                },
                department: async () => {
                    this.selectedDepartment = await this.api(`/api/departments/${this.route.params.departmentId}`);
                },
                history: async () => {
                    this.patientHistory = await this.api(`/api/patients/${this.route.params.patientId}/history`);
                    await this.loadExports(this.route.params.patientId);
                },
                doctorForm: () => this.loadDoctorForm(this.route.params.id),
                patientForm: () => this.loadPatientForm(this.route.params.id),
                profileForm: () => this.loadProfileForm(),
                treatmentForm: () => this.loadTreatmentForm(this.route.params.appointmentId),
            };

            const load = loaders[this.route.name] || (() => this.loadDashboard());
            await load();
        },
        async submitLogin() {
            await this.attempt(async () => {
                await this.api("/api/auth/login", {
                    method: "POST",
                    body: this.authForm,
                });
                this.authForm.password = "";
                await this.initializeAppContext();
                this.pushAlert("Logged in successfully.");
                this.navigate("/dashboard/");
            });
        },
        async submitSignup() {
            await this.attempt(async () => {
                await this.api("/api/auth/signup", {
                    method: "POST",
                    body: this.signupForm,
                });
                this.signupForm = emptySignupForm();
                await this.initializeAppContext();
                this.pushAlert("Account created successfully.");
                this.navigate("/dashboard/");
            });
        },
        async logout() {
            await this.attempt(async () => {
                await this.api("/api/auth/logout", { method: "POST" });
                this.appContext = { user: null, departments: this.appContext.departments };
                this.dashboard = null;
                this.patientSearch.results = [];
                this.pushAlert("Logged out successfully.");
                this.navigate("/");
            });
        },
        runAdminSearch() {
            this.adminSearch.appliedQuery = this.adminSearch.q;
        },
        async runPatientSearch() {
            await this.attempt(async () => {
                const params = new URLSearchParams({
                    q: this.patientSearch.q,
                    department: this.patientSearch.department,
                    date: this.patientSearch.date,
                    slot: this.patientSearch.slot,
                });
                const result = await this.api(`/api/search?${params.toString()}`);
                this.patientSearch.results = result.doctors || [];
            });
        },
        resetPatientSearch() {
            this.patientSearch = emptyPatientSearch();
            this.runPatientSearch();
        },
        async toggleBlacklist(entity, id, shouldBlacklist) {
            await this.attempt(async () => {
                await this.api(`/api/${shouldBlacklist ? "blacklist" : "unblacklist"}/${entity}/${id}`, {
                    method: "POST",
                });
                this.pushAlert(`User ${shouldBlacklist ? "blacklisted" : "restored"} successfully.`);
                await this.loadDashboard();
            });
        },
        async deleteEntity(entity, id) {
            if (!window.confirm(`Delete this ${entity}?`)) return;
            await this.attempt(async () => {
                await this.api(`/api/${entity}/${id}`, { method: "DELETE" });
                this.pushAlert(`${entity} deleted successfully.`);
                await this.loadDashboard();
            });
        },
        async loadDoctorForm(id) {
            this.formMeta = createFormMeta({ id, label: "Doctor" });
            if (!id) {
                this.activeForm = createUserForm({ specialization: "", department_id: "" });
                return;
            }
            const payload = await this.api(`/api/admin/doctors/${id}`);
            this.activeForm = {
                ...payload.doctor,
                password: "",
            };
        },
        async loadPatientForm(id) {
            this.formMeta = createFormMeta({ id, label: "Patient" });
            if (!id) {
                this.activeForm = createUserForm();
                return;
            }
            const payload = await this.api(`/api/admin/patients/${id}`);
            this.activeForm = {
                ...payload.patient,
                password: "",
            };
        },
        async loadProfileForm() {
            const payload = await this.api("/api/profile");
            const profile = payload.profile;
            this.activeForm = {
                ...profile,
                password: "",
                specialization: profile.specialization || "",
                department_id: profile.department_id || "",
            };
            this.formMeta = {
                title: "Edit Profile",
                submitLabel: "Save Profile",
            };
        },
        async submitActiveForm() {
            await this.attempt(async () => {
                const resource = {
                    doctorForm: "doctors",
                    patientForm: "patients",
                }[this.route.name];
                if (resource) {
                    const baseUrl = `/api/admin/${resource}`;
                    const url = this.activeForm.id ? `${baseUrl}/${this.activeForm.id}` : baseUrl;
                    const method = this.activeForm.id ? "PUT" : "POST";
                    await this.api(url, { method, body: this.activeForm });
                } else {
                    await this.api("/api/profile", { method: "PUT", body: this.activeForm });
                }
                this.pushAlert("Saved successfully.");
                await this.initializeAppContext();
                this.navigate("/dashboard/");
            });
        },
        async loadTreatmentForm(appointmentId) {
            const payload = await this.api(`/api/appointments/${appointmentId}/history`);
            this.treatmentForm = {
                appointment: payload.appointment,
                visit_type: payload.appointment.visit_type || "",
                test_done: payload.appointment.test_done || "",
                diagnosis: payload.treatment.diagnosis || "",
                prescription: payload.treatment.prescription || "",
                notes: payload.treatment.notes || "",
                medicines: payload.treatment.medicines || [],
            };
        },
        addMedicineRow() {
            this.treatmentForm.medicines.push(emptyMedicineRow());
        },
        removeMedicineRow(index) {
            this.treatmentForm.medicines.splice(index, 1);
        },
        async submitTreatmentForm() {
            await this.attempt(async () => {
                await this.api(`/api/appointments/${this.treatmentForm.appointment.id}/history`, {
                    method: "PUT",
                    body: {
                        visit_type: this.treatmentForm.visit_type,
                        test_done: this.treatmentForm.test_done,
                        diagnosis: this.treatmentForm.diagnosis,
                        prescription: this.treatmentForm.prescription,
                        notes: this.treatmentForm.notes,
                        medicines: this.treatmentForm.medicines,
                    },
                });
                this.pushAlert("Patient history updated successfully.");
                this.navigate("/dashboard/");
            });
        },
        openPatientHistory(patientId) {
            this.navigate(`/history/patient/${patientId}`);
        },
        async toggleAvailability(date, slot, enabled) {
            await this.attempt(async () => {
                await this.api("/api/doctor/update_availability", {
                    method: "POST",
                    body: {
                        slot: `${date}_${slot}`,
                        enabled,
                    },
                });
                await this.loadDashboard();
            });
        },
        async openAvailabilityModal(doctorId, action, appointmentId = null) {
            await this.attempt(async () => {
                const schedule = await this.api(`/api/doctor/${doctorId}/availability_json`);
                this.availabilityModal = createAvailabilityModal({
                    open: true,
                    doctorId,
                    action,
                    appointmentId,
                    schedule,
                });
            });
        },
        closeAvailabilityModal() {
            this.availabilityModal.open = false;
        },
        availabilityButtonClass(slotRow, slot) {
            const isSelected = this.availabilityModal.selectedDate === slotRow.date && this.availabilityModal.selectedSlot === slot;
            if (isSelected) return "action-btn-positive";
            return slotRow[slot] ? "action-btn-availability" : "action-btn-negative";
        },
        doctorAvailabilityButtonClass(enabled) {
            return enabled ? "action-btn-positive" : "action-btn-negative";
        },
        selectAvailability(date, slot) {
            this.availabilityModal.selectedDate = date;
            this.availabilityModal.selectedSlot = slot;
        },
        async confirmAvailabilityAction() {
            await this.attempt(async () => {
                const body = {
                    new_date: this.availabilityModal.selectedDate,
                    new_time: this.timeForSlot(this.availabilityModal.selectedSlot),
                };
                if (this.availabilityModal.action === "reschedule") {
                    await this.api(`/api/appointment/${this.availabilityModal.appointmentId}/reschedule`, {
                        method: "POST",
                        body,
                    });
                    this.pushAlert("Appointment rescheduled successfully.");
                } else {
                    await this.api("/api/appointments/book", {
                        method: "POST",
                        body: {
                            doctor_id: this.availabilityModal.doctorId,
                            date: this.availabilityModal.selectedDate,
                            time: this.timeForSlot(this.availabilityModal.selectedSlot),
                            visit_type: this.availabilityModal.visitType,
                        },
                    });
                    this.pushAlert("Appointment booked successfully.");
                }
                this.closeAvailabilityModal();
                await this.loadDashboard();
            });
        },
        async cancelAppointment(appointmentId) {
            await this.attempt(async () => {
                await this.api(`/api/appointment/${appointmentId}/cancel`, { method: "POST" });
                this.pushAlert("Appointment cancelled.", "info");
                await this.loadDashboard();
            });
        },
        async markComplete(appointmentId) {
            await this.attempt(async () => {
                await this.api(`/api/doctor/appointment/${appointmentId}/complete`, { method: "POST" });
                this.pushAlert("Appointment marked as completed.");
                await this.loadDashboard();
            });
        },
        async startBatchReport() {
            await this.attempt(async () => {
                await this.queueBatchTask(
                    "/api/batch/reports/daily-summary",
                    "daily-summary",
                    "Daily Summary",
                    "Batch report queued.",
                );
            });
        },
        async startDailyReminders() {
            await this.attempt(async () => {
                await this.queueBatchTask(
                    "/api/batch/reports/daily-reminders",
                    "daily-reminders",
                    "Daily Reminders",
                    "Daily reminders queued.",
                );
            });
        },
        async startMonthlyActivityReport() {
            await this.attempt(async () => {
                await this.queueBatchTask(
                    "/api/batch/reports/monthly-activity",
                    "monthly-activity",
                    "Monthly Activity Reports",
                    "Monthly activity reports queued.",
                );
            });
        },
        async pollBatchTask(taskId) {
            if (this.pollHandle) {
                clearTimeout(this.pollHandle);
            }
            try {
                const payload = await this.api(`/api/batch/tasks/${taskId}`);
                this.batchTask = {
                    ...(this.batchTask || {}),
                    ...payload,
                };
                if (!["SUCCESS", "FAILURE"].includes(payload.state)) {
                    this.pollHandle = setTimeout(() => this.pollBatchTask(taskId), 2000);
                }
            } catch (error) {
                this.handleError(error);
            }
        },
        upsertExportJob(exportJob) {
            const existingIndex = this.exportJobs.findIndex((item) => item.id === exportJob.id);
            if (existingIndex >= 0) {
                this.exportJobs.splice(existingIndex, 1, exportJob);
            } else {
                this.exportJobs.unshift(exportJob);
            }
        },
        async loadExports(patientId = null) {
            await this.attempt(async () => {
                const params = new URLSearchParams();
                if (patientId) {
                    params.set("patient_id", patientId);
                }
                const url = params.toString() ? `/api/exports?${params.toString()}` : "/api/exports";
                const payload = await this.api(url);
                this.exportJobs = payload.exports || [];
            });
        },
        async startTreatmentExport() {
            await this.attempt(async () => {
                const patientId = this.currentExportPatientId();
                const body = patientId ? { patient_id: patientId } : undefined;
                const payload = await this.api("/api/exports/treatments", { method: "POST", body });
                this.pushAlert("Treatment export queued.", "info");
                this.upsertExportJob(payload.export);
                await this.loadExports(patientId);
                this.pollPatientExport(payload.export.id);
            });
        },
        async pollPatientExport(exportId) {
            if (this.exportPollHandle) {
                clearTimeout(this.exportPollHandle);
            }
            try {
                const payload = await this.api(`/api/exports/${exportId}`);
                const exportJob = payload.export;
                this.upsertExportJob(exportJob);
                if (exportJob.status === "Completed") {
                    this.pushAlert("Treatment export is ready.", "success");
                    const patientId = this.currentExportPatientId();
                    await this.loadExports(patientId);
                    if (this.appContext.user?.user_type === "patient") {
                        await this.loadDashboard();
                    }
                    return;
                }
                if (exportJob.status === "Failed") {
                    this.pushAlert(exportJob.error_message || "Treatment export failed.", "danger");
                    return;
                }
                this.exportPollHandle = setTimeout(() => this.pollPatientExport(exportId), 2000);
            } catch (error) {
                this.handleError(error);
            }
        },
    },
});

app.config.compilerOptions.delimiters = ["[[", "]]"];

app.mount("#app");

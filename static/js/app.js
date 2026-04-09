const { createApp } = Vue;

const AppAlerts = {
    template: "#app-alerts-template",
    props: {
        alerts: { type: Array, required: true },
        dismissAlert: { type: Function, required: true },
    },
};

const AppNavbar = {
    template: "#app-navbar-template",
    props: {
        appContext: { type: Object, required: true },
        goHome: { type: Function, required: true },
        navigate: { type: Function, required: true },
        logout: { type: Function, required: true },
    },
};

const PublicHome = {
    template: "#public-home-template",
    props: {
        authMode: { type: String, required: true },
        authForm: { type: Object, required: true },
        signupForm: { type: Object, required: true },
        features: { type: Array, required: true },
        setAuthMode: { type: Function, required: true },
        submitLogin: { type: Function, required: true },
        submitSignup: { type: Function, required: true },
        navigate: { type: Function, required: true },
    },
};

const WorkspaceHeader = {
    template: "#workspace-header-template",
    props: {
        user: { type: Object, required: true },
        viewTitle: { type: String, required: true },
        viewSubtitle: { type: String, required: true },
    },
};

const AdminDashboard = {
    template: "#admin-dashboard-template",
    props: {
        dashboard: { type: Object, required: true },
        adminSearch: { type: Object, required: true },
        filteredAdminDoctors: { type: Array, required: true },
        filteredAdminPatients: { type: Array, required: true },
        filteredAdminAppointments: { type: Array, required: true },
        batchTask: { type: Object, default: null },
        runAdminSearch: { type: Function, required: true },
        navigate: { type: Function, required: true },
        startBatchReport: { type: Function, required: true },
        startDailyReminders: { type: Function, required: true },
        startMonthlyActivityReport: { type: Function, required: true },
        batchTaskStateClass: { type: Function, required: true },
        batchTaskSummary: { type: Function, required: true },
        batchTaskRows: { type: Function, required: true },
        batchTaskRowKey: { type: Function, required: true },
        toggleBlacklist: { type: Function, required: true },
        deleteEntity: { type: Function, required: true },
        openPatientHistory: { type: Function, required: true },
        formatDate: { type: Function, required: true },
        formatTime: { type: Function, required: true },
    },
};

const DoctorDashboard = {
    template: "#doctor-dashboard-template",
    props: {
        dashboard: { type: Object, required: true },
        navigate: { type: Function, required: true },
        formatDate: { type: Function, required: true },
        formatTime: { type: Function, required: true },
        openPatientHistory: { type: Function, required: true },
        openAvailabilityModal: { type: Function, required: true },
        markComplete: { type: Function, required: true },
        cancelAppointment: { type: Function, required: true },
        doctorAvailabilityButtonClass: { type: Function, required: true },
        toggleAvailability: { type: Function, required: true },
    },
};

const PatientDashboard = {
    template: "#patient-dashboard-template",
    props: {
        dashboard: { type: Object, required: true },
        departments: { type: Array, required: true },
        patientSearch: { type: Object, required: true },
        exportJobs: { type: Array, required: true },
        navigate: { type: Function, required: true },
        openPatientHistory: { type: Function, required: true },
        startTreatmentExport: { type: Function, required: true },
        loadExports: { type: Function, required: true },
        formatDate: { type: Function, required: true },
        formatTime: { type: Function, required: true },
        formatDateTime: { type: Function, required: true },
        exportStatusClass: { type: Function, required: true },
        runPatientSearch: { type: Function, required: true },
        resetPatientSearch: { type: Function, required: true },
        openAvailabilityModal: { type: Function, required: true },
        cancelAppointment: { type: Function, required: true },
    },
};

const DepartmentDetails = {
    template: "#department-details-template",
    props: {
        selectedDepartment: { type: Object, required: true },
        navigate: { type: Function, required: true },
        openAvailabilityModal: { type: Function, required: true },
    },
};

const PatientHistory = {
    template: "#patient-history-template",
    props: {
        patientHistory: { type: Object, required: true },
        exportJobs: { type: Array, required: true },
        navigate: { type: Function, required: true },
        startTreatmentExport: { type: Function, required: true },
        canQueueTreatmentExport: { type: Function, required: true },
        loadExports: { type: Function, required: true },
        historyPatientId: { type: Function, required: true },
        formatDate: { type: Function, required: true },
        formatDateTime: { type: Function, required: true },
        exportStatusClass: { type: Function, required: true },
    },
};

const UserForm = {
    template: "#user-form-template",
    props: {
        activeForm: { type: Object, required: true },
        formMeta: { type: Object, required: true },
        departments: { type: Array, required: true },
        showDoctorFields: { type: Boolean, required: true },
        routeName: { type: String, required: true },
        navigate: { type: Function, required: true },
        submitActiveForm: { type: Function, required: true },
    },
};

const TreatmentForm = {
    template: "#treatment-form-template",
    props: {
        treatmentForm: { type: Object, required: true },
        navigate: { type: Function, required: true },
        submitTreatmentForm: { type: Function, required: true },
        addMedicineRow: { type: Function, required: true },
        removeMedicineRow: { type: Function, required: true },
    },
};

const AvailabilityModal = {
    template: "#availability-modal-template",
    props: {
        availabilityModal: { type: Object, required: true },
        closeAvailabilityModal: { type: Function, required: true },
        availabilityButtonClass: { type: Function, required: true },
        selectAvailability: { type: Function, required: true },
        confirmAvailabilityAction: { type: Function, required: true },
    },
};

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
            features: [
                {
                    title: "API-First Workflows",
                    description: "Authentication, dashboards, forms, and appointment actions now run over JSON endpoints instead of server-rendered pages.",
                },
                {
                    title: "Role-Based Operations",
                    description: "Admins manage users, doctors maintain availability and treatment notes, and patients book care from a unified Vue interface.",
                },
                {
                    title: "Theme-Driven Interface",
                    description: "The UI now follows the custom CliniTrak color system and component styling defined in the project stylesheet.",
                },
            ],
            authForm: {
                email: "",
                password: "",
                user_type: "patient",
            },
            signupForm: {
                name: "",
                email: "",
                password: "",
                dob: "",
                contact: "",
            },
            adminSearch: {
                q: "",
                appliedQuery: "",
            },
            patientSearch: {
                q: "",
                department: "",
                date: "",
                slot: "",
                results: [],
            },
            activeForm: null,
            formMeta: {
                title: "",
                submitLabel: "",
            },
            selectedDepartment: null,
            patientHistory: null,
            treatmentForm: {
                appointment: null,
                visit_type: "",
                test_done: "",
                diagnosis: "",
                prescription: "",
                notes: "",
                medicines: [],
            },
            availabilityModal: {
                open: false,
                doctorId: null,
                action: "book",
                appointmentId: null,
                schedule: [],
                selectedDate: "",
                selectedSlot: "",
                visitType: "Checkup",
            },
            batchTask: null,
            pollHandle: null,
            exportJobs: [],
            exportPollHandle: null,
        };
    },
    computed: {
        loginLabel() {
            const role = this.authForm.user_type

            if (!role) return "Login"

            let ret = "Login As " + role.charAt(0).toUpperCase() + role.slice(1);
            console.log(ret);

            return ret
        },
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
            if (this.route.name === "doctorForm") return true;
            return this.route.name === "profileForm" && this.appContext.user?.user_type === "doctor";
        },
        adminSearchTerm() {
            return (this.adminSearch.appliedQuery || "").trim().toLowerCase();
        },
        filteredAdminDoctors() {
            const doctors = this.dashboard?.doctors || [];
            if (!this.adminSearchTerm) return doctors;
            return doctors.filter((doctor) => this.matchesAdminSearch(doctor, [
                doctor.name,
                doctor.email,
                doctor.contact,
                doctor.specialization,
                doctor.department_name,
                doctor.is_blacklisted ? "blacklisted" : "active",
            ]));
        },
        filteredAdminPatients() {
            const patients = this.dashboard?.patients || [];
            if (!this.adminSearchTerm) return patients;
            return patients.filter((patient) => this.matchesAdminSearch(patient, [
                patient.name,
                patient.email,
                patient.contact,
                patient.is_blacklisted ? "blacklisted" : "active",
            ]));
        },
        filteredAdminAppointments() {
            const appointments = this.dashboard?.upcoming_appointments || [];
            if (!this.adminSearchTerm) return appointments;
            return appointments.filter((appointment) => this.matchesAdminSearch(appointment, [
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
            ]));
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
        handleError(error) {
            this.pushAlert(error.message || "Unexpected error.", "danger");
        },
        setAuthMode(mode) {
            this.authMode = mode;
            this.navigate(mode === "signup" ? "/signup/" : "/login/");
        },
        resolveRoute(pathname) {
            const clean = pathname.length > 1 ? pathname.replace(/\/$/, "") : pathname;
            const patterns = [
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

            for (const pattern of patterns) {
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
            if (slot === "morning") return "09:00";
            if (slot === "afternoon") return "13:00";
            return "17:00";
        },
        historyPatientId() {
            return this.patientHistory?.patient?.id || null;
        },
        currentExportPatientId() {
            if (this.route.name === "history") {
                return this.historyPatientId();
            }
            if (this.appContext.user?.user_type === "patient") {
                return this.appContext.user.id;
            }
            return null;
        },
        canQueueTreatmentExport() {
            return Boolean(this.currentExportPatientId());
        },
        exportStatusClass(status) {
            if (status === "Completed") return "status-pill-success";
            if (status === "Failed") return "status-pill-danger";
            if (status === "Processing") return "status-pill-primary";
            return "status-pill-secondary";
        },
        batchTaskStateClass(state) {
            if (state === "SUCCESS") return "status-pill-success";
            if (state === "FAILURE") return "status-pill-danger";
            if (state === "STARTED" || state === "PROGRESS") return "status-pill-primary";
            return "status-pill-secondary";
        },
        batchTaskSummary(task) {
            if (!task?.result) return [];
            if (task.kind === "daily-summary") {
                return [
                    { label: "Doctors", value: task.result.totals?.doctors ?? 0 },
                    { label: "Patients", value: task.result.totals?.patients ?? 0 },
                    { label: "Appointments Today", value: task.result.totals?.appointments_today ?? 0 },
                    { label: "Booked", value: task.result.statuses?.booked ?? 0 },
                    { label: "Completed", value: task.result.statuses?.completed ?? 0 },
                    { label: "Cancelled", value: task.result.statuses?.cancelled ?? 0 },
                ];
            }
            if (task.kind === "daily-reminders") {
                return [
                    { label: "Date", value: task.result.date || "N/A" },
                    { label: "Appointments Considered", value: task.result.appointments_considered ?? 0 },
                    { label: "Notifications Sent", value: task.result.notifications_sent ?? 0 },
                ];
            }
            if (task.kind === "monthly-activity") {
                return [
                    { label: "Period Start", value: task.result.period_start || "N/A" },
                    { label: "Period End", value: task.result.period_end || "N/A" },
                    { label: "Reports Generated", value: task.result.reports_generated ?? 0 },
                    { label: "Reports Delivered", value: task.result.reports_delivered ?? 0 },
                ];
            }
            return [];
        },
        batchTaskRows(task) {
            if (!task?.result) return [];
            if (task.kind === "daily-reminders") {
                return task.result.reminders || [];
            }
            if (task.kind === "monthly-activity") {
                return task.result.items || [];
            }
            return [];
        },
        batchTaskRowKey(task, taskRow, index) {
            if (task.kind === "daily-reminders") {
                return taskRow.appointment_id || index;
            }
            if (task.kind === "monthly-activity") {
                return taskRow.doctor_id || index;
            }
            return index;
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
            this.treatmentForm = {
                appointment: null,
                visit_type: "",
                test_done: "",
                diagnosis: "",
                prescription: "",
                notes: "",
                medicines: [],
            };
        },
        async initializeAppContext() {
            this.loading = true;
            try {
                const data = await this.api("/api/app-context");
                this.appContext = data;
                this.route = this.resolveRoute(window.location.pathname);
                await this.loadRouteData();
            } catch (error) {
                this.handleError(error);
            } finally {
                this.loading = false;
            }
        },
        async loadDashboard() {
            this.dashboard = await this.api("/api/dashboard");
            if (this.appContext.user?.user_type === "patient") {
                this.exportJobs = this.dashboard.export_jobs || [];
            }
        },
        async loadRouteData() {
            this.resetTransientState();
            if (!this.appContext.user) {
                return;
            }

            if (this.route.name === "dashboard") {
                await this.loadDashboard();
                if (this.appContext.user.user_type === "patient" && !this.patientSearch.results.length) {
                    await this.runPatientSearch();
                }
                return;
            }

            if (this.route.name === "department") {
                const payload = await this.api(`/api/departments/${this.route.params.departmentId}`);
                this.selectedDepartment = payload;
                return;
            }

            if (this.route.name === "history") {
                this.patientHistory = await this.api(`/api/patients/${this.route.params.patientId}/history`);
                await this.loadExports(this.route.params.patientId);
                return;
            }

            if (this.route.name === "doctorForm") {
                await this.loadDoctorForm(this.route.params.id);
                return;
            }

            if (this.route.name === "patientForm") {
                await this.loadPatientForm(this.route.params.id);
                return;
            }

            if (this.route.name === "profileForm") {
                await this.loadProfileForm();
                return;
            }

            if (this.route.name === "treatmentForm") {
                await this.loadTreatmentForm(this.route.params.appointmentId);
                return;
            }

            await this.loadDashboard();
        },
        async submitLogin() {
            try {
                await this.api("/api/auth/login", {
                    method: "POST",
                    body: this.authForm,
                });
                this.authForm.password = "";
                await this.initializeAppContext();
                this.pushAlert("Logged in successfully.");
                this.navigate("/dashboard/");
            } catch (error) {
                this.handleError(error);
            }
        },
        async submitSignup() {
            try {
                await this.api("/api/auth/signup", {
                    method: "POST",
                    body: this.signupForm,
                });
                this.signupForm = { name: "", email: "", password: "", dob: "", contact: "" };
                await this.initializeAppContext();
                this.pushAlert("Account created successfully.");
                this.navigate("/dashboard/");
            } catch (error) {
                this.handleError(error);
            }
        },
        async logout() {
            try {
                await this.api("/api/auth/logout", { method: "POST" });
                this.appContext = { user: null, departments: this.appContext.departments };
                this.dashboard = null;
                this.patientSearch.results = [];
                this.pushAlert("Logged out successfully.");
                this.navigate("/");
            } catch (error) {
                this.handleError(error);
            }
        },
        async runAdminSearch() {
            this.adminSearch.appliedQuery = this.adminSearch.q;
        },
        async runPatientSearch() {
            try {
                const params = new URLSearchParams({
                    q: this.patientSearch.q,
                    department: this.patientSearch.department,
                    date: this.patientSearch.date,
                    slot: this.patientSearch.slot,
                });
                const result = await this.api(`/api/search?${params.toString()}`);
                this.patientSearch.results = result.doctors || [];
            } catch (error) {
                this.handleError(error);
            }
        },
        resetPatientSearch() {
            this.patientSearch = { q: "", department: "", date: "", slot: "", results: [] };
            this.runPatientSearch();
        },
        async toggleBlacklist(entity, id, shouldBlacklist) {
            try {
                await this.api(`/api/${shouldBlacklist ? "blacklist" : "unblacklist"}/${entity}/${id}`, {
                    method: "POST",
                });
                this.pushAlert(`User ${shouldBlacklist ? "blacklisted" : "restored"} successfully.`);
                await this.loadDashboard();
            } catch (error) {
                this.handleError(error);
            }
        },
        async deleteEntity(entity, id) {
            if (!window.confirm(`Delete this ${entity}?`)) return;
            try {
                await this.api(`/api/${entity}/${id}`, { method: "DELETE" });
                this.pushAlert(`${entity} deleted successfully.`);
                await this.loadDashboard();
            } catch (error) {
                this.handleError(error);
            }
        },
        async loadDoctorForm(id) {
            this.formMeta = {
                title: id ? "Edit Doctor" : "Create Doctor",
                submitLabel: id ? "Update Doctor" : "Create Doctor",
            };
            if (!id) {
                this.activeForm = {
                    id: null,
                    name: "",
                    email: "",
                    password: "",
                    dob: "",
                    contact: "",
                    specialization: "",
                    department_id: "",
                };
                return;
            }
            const payload = await this.api(`/api/admin/doctors/${id}`);
            this.activeForm = {
                ...payload.doctor,
                password: "",
            };
        },
        async loadPatientForm(id) {
            this.formMeta = {
                title: id ? "Edit Patient" : "Create Patient",
                submitLabel: id ? "Update Patient" : "Create Patient",
            };
            if (!id) {
                this.activeForm = {
                    id: null,
                    name: "",
                    email: "",
                    password: "",
                    dob: "",
                    contact: "",
                };
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
            try {
                if (this.route.name === "doctorForm") {
                    const url = this.activeForm.id ? `/api/admin/doctors/${this.activeForm.id}` : "/api/admin/doctors";
                    const method = this.activeForm.id ? "PUT" : "POST";
                    await this.api(url, { method, body: this.activeForm });
                } else if (this.route.name === "patientForm") {
                    const url = this.activeForm.id ? `/api/admin/patients/${this.activeForm.id}` : "/api/admin/patients";
                    const method = this.activeForm.id ? "PUT" : "POST";
                    await this.api(url, { method, body: this.activeForm });
                } else {
                    await this.api("/api/profile", { method: "PUT", body: this.activeForm });
                }
                this.pushAlert("Saved successfully.");
                await this.initializeAppContext();
                this.navigate("/dashboard/");
            } catch (error) {
                this.handleError(error);
            }
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
            this.treatmentForm.medicines.push({
                name: "",
                morning: 0,
                afternoon: 0,
                night: 0,
                duration_days: 1,
                instructions: "",
            });
        },
        removeMedicineRow(index) {
            this.treatmentForm.medicines.splice(index, 1);
        },
        async submitTreatmentForm() {
            try {
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
            } catch (error) {
                this.handleError(error);
            }
        },
        async openPatientHistory(patientId) {
            this.navigate(`/history/patient/${patientId}`);
        },
        async toggleAvailability(date, slot, enabled) {
            try {
                await this.api("/api/doctor/update_availability", {
                    method: "POST",
                    body: {
                        slot: `${date}_${slot}`,
                        enabled,
                    },
                });
                await this.loadDashboard();
            } catch (error) {
                this.handleError(error);
            }
        },
        async openAvailabilityModal(doctorId, action, appointmentId = null) {
            try {
                const schedule = await this.api(`/api/doctor/${doctorId}/availability_json`);
                this.availabilityModal = {
                    open: true,
                    doctorId,
                    action,
                    appointmentId,
                    schedule,
                    selectedDate: "",
                    selectedSlot: "",
                    visitType: "Checkup",
                };
            } catch (error) {
                this.handleError(error);
            }
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
            try {
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
            } catch (error) {
                this.handleError(error);
            }
        },
        async cancelAppointment(appointmentId) {
            try {
                await this.api(`/api/appointment/${appointmentId}/cancel`, { method: "POST" });
                this.pushAlert("Appointment cancelled.", "info");
                await this.loadDashboard();
            } catch (error) {
                this.handleError(error);
            }
        },
        async markComplete(appointmentId) {
            try {
                await this.api(`/api/doctor/appointment/${appointmentId}/complete`, { method: "POST" });
                this.pushAlert("Appointment marked as completed.");
                await this.loadDashboard();
            } catch (error) {
                this.handleError(error);
            }
        },
        async startBatchReport() {
            try {
                await this.queueBatchTask(
                    "/api/batch/reports/daily-summary",
                    "daily-summary",
                    "Daily Summary",
                    "Batch report queued.",
                );
            } catch (error) {
                this.handleError(error);
            }
        },
        async startDailyReminders() {
            try {
                await this.queueBatchTask(
                    "/api/batch/reports/daily-reminders",
                    "daily-reminders",
                    "Daily Reminders",
                    "Daily reminders queued.",
                );
            } catch (error) {
                this.handleError(error);
            }
        },
        async startMonthlyActivityReport() {
            try {
                await this.queueBatchTask(
                    "/api/batch/reports/monthly-activity",
                    "monthly-activity",
                    "Monthly Activity Reports",
                    "Monthly activity reports queued.",
                );
            } catch (error) {
                this.handleError(error);
            }
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
            try {
                const params = new URLSearchParams();
                if (patientId) {
                    params.set("patient_id", patientId);
                }
                const url = params.toString() ? `/api/exports?${params.toString()}` : "/api/exports";
                const payload = await this.api(url);
                this.exportJobs = payload.exports || [];
            } catch (error) {
                this.handleError(error);
            }
        },
        async startTreatmentExport() {
            try {
                const patientId = this.currentExportPatientId();
                const body = patientId ? { patient_id: patientId } : undefined;
                const payload = await this.api("/api/exports/treatments", { method: "POST", body });
                this.pushAlert("Treatment export queued.", "info");
                this.upsertExportJob(payload.export);
                await this.loadExports(patientId);
                this.pollPatientExport(payload.export.id);
            } catch (error) {
                this.handleError(error);
            }
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

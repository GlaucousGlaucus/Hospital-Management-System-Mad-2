const { createApp } = Vue;

createApp({
    delimiters: ["[[", "]]"],
    data() {
        return {
            loading: true,
            bootstrap: {
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
                    title: "Operational Stack Compliance",
                    description: "Flask, Vue, Bootstrap, SQLite, Redis, and Celery are now the active implementation path in this repository.",
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
                results: null,
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
            if (!this.bootstrap.user) {
                return "Single page hospital operations.";
            }
            const role = this.bootstrap.user.user_type;
            if (this.route.name === "dashboard") {
                if (role === "admin") return "Manage doctors, patients, appointments, and batch jobs.";
                if (role === "doctor") return "Track appointments, update treatment records, and maintain availability.";
                return "Book appointments, review departments, and manage your profile.";
            }
            return "Vue-driven frontend on top of the Flask API.";
        },
        showDoctorFields() {
            if (this.route.name === "doctorForm") return true;
            return this.route.name === "profileForm" && this.bootstrap.user?.user_type === "doctor";
        },
    },
    mounted() {
        window.addEventListener("popstate", this.handlePopState);
        this.bootstrapApp();
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

            return { name: this.bootstrap.user ? "dashboard" : "home", params: {} };
        },
        navigate(path, pushState = true) {
            if (pushState) {
                window.history.pushState({}, "", path);
            }
            this.route = this.resolveRoute(path);
            this.loadRouteData();
        },
        goHome() {
            this.navigate(this.bootstrap.user ? "/dashboard/" : "/");
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
            if (this.bootstrap.user?.user_type === "patient") {
                return this.bootstrap.user.id;
            }
            return null;
        },
        canQueueTreatmentExport() {
            return Boolean(this.currentExportPatientId());
        },
        exportStatusClass(status) {
            if (status === "Completed") return "text-bg-success";
            if (status === "Failed") return "text-bg-danger";
            if (status === "Processing") return "text-bg-primary";
            return "text-bg-secondary";
        },
        batchTaskStateClass(state) {
            if (state === "SUCCESS") return "text-bg-success";
            if (state === "FAILURE") return "text-bg-danger";
            if (state === "STARTED" || state === "PROGRESS") return "text-bg-primary";
            return "text-bg-secondary";
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
        batchTaskRowKey(task, row, index) {
            if (task.kind === "daily-reminders") {
                return row.appointment_id || index;
            }
            if (task.kind === "monthly-activity") {
                return row.doctor_id || index;
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
        async bootstrapApp() {
            this.loading = true;
            try {
                const data = await this.api("/api/bootstrap");
                this.bootstrap = data;
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
            if (this.bootstrap.user?.user_type === "patient") {
                this.exportJobs = this.dashboard.export_jobs || [];
            }
        },
        async loadRouteData() {
            this.resetTransientState();
            if (!this.bootstrap.user) {
                return;
            }

            if (this.route.name === "dashboard") {
                await this.loadDashboard();
                if (this.bootstrap.user.user_type === "patient" && !this.patientSearch.results.length) {
                    await this.runPatientSearch(false);
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
                await this.bootstrapApp();
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
                await this.bootstrapApp();
                this.pushAlert("Account created successfully.");
                this.navigate("/dashboard/");
            } catch (error) {
                this.handleError(error);
            }
        },
        async logout() {
            try {
                await this.api("/api/auth/logout", { method: "POST" });
                this.bootstrap = { user: null, departments: this.bootstrap.departments };
                this.dashboard = null;
                this.patientSearch.results = [];
                this.pushAlert("Logged out successfully.");
                this.navigate("/");
            } catch (error) {
                this.handleError(error);
            }
        },
        async runAdminSearch() {
            try {
                const params = new URLSearchParams({ q: this.adminSearch.q });
                this.adminSearch.results = await this.api(`/api/search?${params.toString()}`);
            } catch (error) {
                this.handleError(error);
            }
        },
        async runPatientSearch(notify = true) {
            try {
                const params = new URLSearchParams({
                    q: this.patientSearch.q,
                    department: this.patientSearch.department,
                    date: this.patientSearch.date,
                    slot: this.patientSearch.slot,
                });
                const result = await this.api(`/api/search?${params.toString()}`);
                this.patientSearch.results = result.doctors || [];
                if (notify) {
                    this.pushAlert(`Found ${this.patientSearch.results.length} doctor(s).`, "info");
                }
            } catch (error) {
                this.handleError(error);
            }
        },
        resetPatientSearch() {
            this.patientSearch = { q: "", department: "", date: "", slot: "", results: [] };
            this.runPatientSearch(false);
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
                await this.bootstrapApp();
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
                this.pushAlert("Availability updated.");
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
        availabilityButtonClass(row, slot) {
            const isSelected = this.availabilityModal.selectedDate === row.date && this.availabilityModal.selectedSlot === slot;
            if (isSelected) return "btn-success";
            return row[slot] ? "btn-outline-success" : "btn-outline-danger";
        },
        doctorAvailabilityButtonClass(enabled) {
            return enabled ? "btn-success" : "btn-outline-danger";
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
                    if (this.bootstrap.user?.user_type === "patient") {
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
}).mount("#app");

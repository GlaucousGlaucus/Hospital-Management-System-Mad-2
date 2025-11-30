export function createPersonListCard(entity, role) {

    const bg = entity.is_blacklisted ? `style="background:#fff0f0;"` : "";

    const blacklistBtn = entity.is_blacklisted
        ? createIconButton("unblacklist", role, entity.id, "block")   // same icon for minimal change
        : createIconButton("blacklist", role, entity.id, "block");

    return `
    <div class="card-item" data-id="${entity.id}" ${bg}>
        <span class="card-title">${entity.name}</span>

        <div class="profile-picture">
            <img src="/static/Resources/logo.png" height="200" width="200" style="border-radius: 50%;" />
        </div>

        <div class="card-buttons">
            ${createIconButton("edit", role, entity.id, "edit")}
            ${createIconButton("delete", role, entity.id, "person_remove")}
            ${blacklistBtn}
        </div>
    </div>
  `;
}


export function createAppointmentRow(appt, hide = false) {

    const actionCell = hide ? "" : `
        <td id="buttons-actions">
            <div class="card-buttons">
                <button class="btn btn-filled"
                        style="background-color:#fff3cd; color:#856404;"
                        data-action="reschedule"
                        data-id="${appt.id}"
                        data-doctor="${appt.doctor_id}">
                    Reschedule
                </button>

                <button class="btn btn-filled"
                        style="background-color:#d4edda; color:#155724;"
                        data-action="complete"
                        data-id="${appt.id}">
                    Complete
                </button>

                <button class="btn btn-filled"
                        style="background-color:#f8d7da; color:#721c24;"
                        data-action="cancel"
                        data-id="${appt.id}">
                    Cancel
                </button>
            </div>
        </td>
    `;

    return `
        <tr>
            <td>${appt.id}</td>
            <td>${appt.patient_name}</td>
            <td>${appt.doctor_name}</td>
            <td>${appt.doctor_dep}</td>
            <td>
                <a class="btn btn-outline"
                   href="/api/patient/${appt.patient_id}/history">
                    View
                </a>
            </td>
            ${actionCell}
        </tr>
    `;
}

export function createIconButton(action, type, id, icon) {
    return `
    <button class="btn btn-icon" data-action="${action}" data-type="${type}" data-id="${id}" title="${action}">
        <span class="material-symbols-outlined">${icon}</span>
    </button>
  `;
}

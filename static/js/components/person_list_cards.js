export function createPersonListCard(entity, role) {
    return `
    <div class="card-item" data-id="${entity.id}">
        <span class="card-title">${entity.name}</span>

        <div class="profile-picture">
            <img src="/static/Resources/logo.png" height="200" width="200" style="border-radius: 50%;" />
        </div>

        <div class="card-buttons">
            ${createIconButton("edit", role, entity.id, "edit")}
            ${createIconButton("delete", role, entity.id, "person_remove")}
            ${createIconButton("blacklist", role, entity.id, "block")}
        </div>
    </div>
  `;
}

export function createAppointmentRow(data) {
    return `
    <tr>
        <td>${data.id}</td>
        <td>${data.patient_name ?? "N/A"}</td>
        <td>${data.doctor_name ?? "N/A"}</td>
        <td>${data.doctor_dep ?? "N/A"}</td>
        <td>
            <a href="/api/patient/${data.patient_id}/history"
               class="btn btn-filled btn-view">View</a>
        </td>
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

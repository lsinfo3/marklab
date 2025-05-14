let copyJsonTimeoutID;
let copyJsonPreviousID;

// Remove the stored JSON every time the user opens a page with the task table
sessionStorage.removeItem("editJSON");

document.addEventListener("DOMContentLoaded", function () {
    const selectionVisible = document.getElementById("selectionVisible");
    const offsetTop = selectionVisible.offsetTop;
    const offsetLeft = selectionVisible.offsetLeft;
    const width = selectionVisible.offsetWidth

    window.addEventListener("scroll", function () {
        if (window.scrollY > offsetTop) {
            selectionVisible.style.position = "fixed";
            selectionVisible.style.top = "0";
            selectionVisible.style.left = offsetLeft + "px";
            selectionVisible.style.width = width + "px";
        } else {
            selectionVisible.style.position = "relative";
            selectionVisible.style.left = "";
            selectionVisible.style.width = "";
        }
    });
});

let isTableVisible = false;
function toggleVisibilityOfTable() {
    let table = document.getElementById('taskTableArchivedTasks');
    let toggleVisibilityOfTableIcon = document.getElementById('toggleVisibilityOfTableIcon');
    if (isTableVisible) {
        table.classList.add('table-not-visible');
        toggleVisibilityOfTableIcon.classList.remove('bi-arrow-up');
        toggleVisibilityOfTableIcon.classList.add('bi-arrow-down');
    } else {
        table.classList.remove('table-not-visible');
        toggleVisibilityOfTableIcon.classList.remove('bi-arrow-down');
        toggleVisibilityOfTableIcon.classList.add('bi-arrow-up');
    }
    isTableVisible = !isTableVisible;
}


function copyJson(id) {
    const buttonText = "Copy";
    const buttonTextClicked = "Copied"

    const row = document.getElementById("taskRow" + id);
    const copyJsonButton = row.querySelector(".copyJsonButton");

    if (copyJsonPreviousID && copyJsonPreviousID !== id) {
        const previousRow = document.getElementById("taskRow" + copyJsonPreviousID);
        const copyJsonPreviousButton = previousRow.querySelector(".copyJsonButton");

        if (copyJsonPreviousButton.textContent === buttonTextClicked) {
            clearTimeout(copyJsonTimeoutID)
            copyJsonPreviousButton.textContent = buttonText
        }
    } else if (copyJsonPreviousID === id && copyJsonButton.textContent === buttonTextClicked) {
        clearTimeout(copyJsonTimeoutID)
    }

    copyJsonButton.textContent = buttonTextClicked
    copyJsonTimeoutID = setTimeout(function () {
        copyJsonButton.textContent = buttonText
    }.bind(copyJsonButton), 2000)

    navigator.clipboard.writeText(row.dataset.json);
    copyJsonPreviousID = id;
}

function deleteAndEditTask(id, status, deleteTaskURL, csrfToken, createTaskURL) {
    const row = document.getElementById("taskRow" + id);
    const editJSON = row.dataset.json;

    const editTaskButton = row.querySelector(".editTaskButton");
    editTaskButton.disabled = true;

    if(status === "pending" || status === "scheduled-pending") {
        fetch(deleteTaskURL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: '{"is_edit": true}'
        }).then(response => response.json()).then(response => {
            if(response.success) {
                // Task deleted, open create task form with prefilled fields now
                editTask(editJSON, createTaskURL);
            } else {
                // Task status changed, refresh the page
                window.location.reload();
            }
        });
    } else {
        editTask(editJSON, createTaskURL);
    }
}

function editTask(editJSON, createTaskURL) {
    sessionStorage.setItem("editJSON", editJSON);
    window.location.href = createTaskURL;
}

function runSelectionAction(tableId, action) {
    const table = $(tableId).DataTable()
    // get the selected rows from the first column and 6th column
    const selectedRows = table.column(0).checkboxes.selected();

    const ids = [];

    for (let i = 0; i < selectedRows.length; i++) {
        const id = selectedRows[i];
        const taskRow = document.getElementById("taskRow" + id);

        if(action === "download" && (!taskRow.dataset.hasResult || taskRow.dataset.hasResult !== "true")) {
            alert('No result available for task #' + id + '!');
            return;
        } else if(action === "delete" && taskRow.dataset.status !== "pending" && taskRow.dataset.status !== "completed" && taskRow.dataset.status !== "scheduled-completed" && taskRow.dataset.status !== "failed" && taskRow.dataset.status !== "scheduled-failed") {
            alert('Task #' + id + ' is still running and cannot be deleted!');
            return;
        }

        ids.push(selectedRows[i]);
    }

    if (ids.length === 0) {
        alert('No tasks selected!');
        return;
    }

    // Send the list of task IDs to the server to get a zip file
    const form = document.getElementById('downloadResultsForm');
    form.task_ids.value = JSON.stringify({task_ids: ids});
    form.selected_action.value = action;
    form.submit();
}

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("filter_date_form").addEventListener("submit", function(event) {
        let startDate = document.getElementById('task_table_filter_start_date').value;
        let endDate = document.getElementById('task_table_filter_end_date').value;

        startDate = new Date(startDate);
        endDate = new Date(endDate);

        if (endDate < startDate) {
            alert("The end date cannot be before the start date!");
            event.preventDefault();
        }
    });
})

function setDefaultFilters() {
    const URLParams = new URLSearchParams(window.location.search);

    const startDate = URLParams.get("task_table_filter_start_date");
    const endDate = URLParams.get("task_table_filter_end_date");
    const status = URLParams.get("filter_task_status_select");

    if (startDate || endDate || status) {
        let submitFilterDateButton = document.getElementById("submit_filter_date_button");
        submitFilterDateButton.classList.add("btn-warning");

        let clearFilterDateButton = document.getElementById("clear_filter_date_button");
        clearFilterDateButton.disabled = false;
    }

    const currentDate = new Date();
    const formattedDateToday = currentDate.toISOString().split('T')[0];

    if (startDate) {
        document.getElementById('task_table_filter_start_date').value = startDate;
    }

    if (endDate) {
        document.getElementById('task_table_filter_end_date').value = endDate;
    } else {
        document.getElementById('task_table_filter_end_date').value = formattedDateToday;
    }

    if (status) {
        let select = document.getElementById('filter_task_status_select');
        let options = Array.from(select.options).map(option => option.value);
        if (options.includes(status)) {
            select.value = status;
        } else {
            document.getElementById("filter_task_status_select_hidden").value = "all";
        }
    }

    document.getElementById('task_table_filter_start_date').max = formattedDateToday;
    document.getElementById('task_table_filter_end_date').max = formattedDateToday;
}

window.onload = function() {
    setDefaultFilters();
}
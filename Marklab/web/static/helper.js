function appendAlert(message, type, placeholderId) {
    const alertPlaceholder = document.getElementById(placeholderId)
    const wrapper = document.createElement('div')
    wrapper.innerHTML = [
        `<div class="alert alert-${type} alert-dismissible" role="alert">`,
        `   <div>${message}</div>`,
        '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
        '</div>'
    ].join('')

    alertPlaceholder.append(wrapper)
}

function showDataTable(id, number_pages=10) {
    $(document).ready(function () {
        var table = $(id).DataTable({
            paging: true,
            searching: true,
            lengthChange: true,
            order: [[2, 'desc']],
            pageLength: number_pages,
            dom: "<'top flex align-items-center justify-content-between'lipf>t<'bottom flex align-items-center justify-content-between'lip>",
            select: {
                style: 'multi',
                selector: 'td:first-child'
            },
            lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "all"]],
            columnDefs: [
                {
                    checkboxes: {
                        selectRow: true
                    },
                    targets: 0
                },
                {
                    width: '0%',
                    targets: [2, 7]
                },
                {
                    orderable: false,
                    targets: [0, 1, 4, 5, 6, 7, 8]
                }
            ]
        });

        // Update download button style on select or deselect checkboxes from the first column
        table.on(
            'select deselect',
            function() {
                updateSelectionButtonStyle(table);
            }
        );
    });
}

function updateSelectionButtonStyle(table) {
    const selectedRows = table.column(0).checkboxes.selected();

    const downloadSelected = document.getElementById("downloadSelected");
    const deleteSelected = document.getElementById("deleteSelected");

    if (selectedRows.length > 0) {
        downloadSelected.classList.remove('btn-light');
        downloadSelected.classList.add('btn-success');

        deleteSelected.classList.remove('btn-light');
        deleteSelected.classList.add('btn-danger');
    } else {
        downloadSelected.classList.remove('btn-success');
        downloadSelected.classList.add('btn-light');

        deleteSelected.classList.remove('btn-danger');
        deleteSelected.classList.add('btn-light');
    }
}

function fetchDataWithConfirmation(url, headers, method, confirmationMessage = "Are you sure?") {
    if (confirm(confirmationMessage)) {
        fetch(url, {
            method: method,
            headers: headers,
        }).then(response => response.json()).then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                alert(data.message);
            }
        }).catch(error => alert(error))
    }
}

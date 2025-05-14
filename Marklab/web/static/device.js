function downloadFile(id) {
    // Hier wird der Download-Link für die Datei aufgerufen
    window.location.href = '{% url "download" task_id=0 %}'.replace('0', id);
}

function deleteTask(url, csrf_token) {
    // ask the user if he is sure to delete the task
    fetchDataWithConfirmation(
        url,
        {'X-CSRFToken': csrf_token},
        'DELETE',
        'Are you sure you want to delete this task?',
    )
}

function archiveTask(url, csrf_token) {
    // ask the user if he is sure to archive the task
    fetchDataWithConfirmation(
        url,
        {'X-CSRFToken': csrf_token},
        'DELETE',
        'Are you sure you want to archive the task?',
    )
}

function undoArchivingTask(url, csrf_token) {
    // ask the user if he is sure to undo the archiving of the task
    fetchDataWithConfirmation(
        url,
        {'X-CSRFToken': csrf_token},
        'DELETE',
        'Are you sure you want to undo the archiving of the task?',
    )
}

function rerunTask(url, csrf_token){
    // ask the user if he is sure to rerun the task
    fetchDataWithConfirmation(
        url,
        {'X-CSRFToken': csrf_token},
        'POST',
        'Are you sure you want to rerun this task?',
    )
}

function stopTask(url, csrf_token){
    // ask the user if he is sure to stop the task
    fetchDataWithConfirmation(
        url,
        {'X-CSRFToken': csrf_token},
        'POST',
        'Are you sure you want to stop this task? This process cannot be undone and will take some time.',
    )
}

function uploadZipFile(url, csrf_token) {
    // Hier wird der Upload-Link für die Datei aufgerufen
    // check if file is zip
    let file = document.getElementById('id_file').files[0];

    if (file === undefined || file.name.split('.').pop() !== 'zip') {
        alert('Please upload a zip file');
        return;
    }
    //'{% url "upload" device_id=device.id %}'
    fetch(url, {
        method: 'POST',
        headers: {'X-CSRFToken': csrf_token},
        body: new FormData(document.getElementById('uploadModal').querySelector('form'))
    }).then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.reload();
            } else {
                 window.location.reload();
                //alert(data.message);
            }
        }).catch(error => alert(error))

}
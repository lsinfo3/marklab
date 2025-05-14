const iot_modem = "Quectel_BG96";
const other_modem = "Quectel_EC21";

//region form interaction
function operatorMode() {
    const operator_mode = document.getElementById('operator_mode').value;
    document.getElementById('operator').disabled = operator_mode !== 'manual';
    if (operator_mode !== 'manual') {
        document.getElementById('operator').value = '';
    }

    if (operator_mode === 'any') {
        document.getElementById('access_technology').value = 'all';
        document.getElementById('access_technology').disabled = true;
    }else{
        document.getElementById('access_technology').disabled = false;
    }

    updateOperatorPreset();
}

function modemChange(modem) {
    //document.getElementById('access_technology').disabled = modem !== modem_name;

    document.getElementById('access_technology').disabled = false;
    document.getElementById('act_config').hidden = modem !== iot_modem;
    document.getElementById('gsm_band').value = '';
    document.getElementById('catm1_band').value = '';
    document.getElementById('nbiot_band').value = '';
    document.getElementById('access_technology').value = 'all';
    //if modem = iot_modem the select options should be: all, catm1, nbiot
    //else the select options should be: all, gsm, catm1, nbiot
    let act = document.getElementById('access_technology');
    act.innerHTML = '';
    let options = [['All','all']];
    if (modem === iot_modem) {
        options.push(['2G','0']);
        options.push(['LTE-M','8']);
        options.push(['NB-IoT','9']);
    } else {
        options.push(['2G','0']);
        options.push(['3G','2']);
        options.push(['LTE','7']);
    }
    for (let i = 0; i < options.length; i++) {
        let option = document.createElement('option');
        option.value = options[i][1];
        option.text = options[i][0];
        act.appendChild(option);
    }

    const operator_from_scan_results = document.getElementById('operator_from_scan_results');
    operator_from_scan_results.disabled = false;
    operator_from_scan_results.innerText = "From scan results";

    // If modem is changed and operator mode is any, then disable access technology
    operatorMode();
}

function actChange() {
    updateOperatorPreset();
}

function updateOperatorPreset() {
    const operator_mode = document.getElementById('operator_mode').value;
    const operator_preset_section = document.getElementById('operator_preset_section');
    const operator_manual_section = document.getElementById('operator_manual_section');

    if(operator_mode !== "from_scan_results") {
        operator_preset_section.hidden = true;
        operator_manual_section.hidden = false;
        return;
    }

    operator_preset_section.querySelectorAll('.operator_preset_list').forEach(preset_list => preset_list.hidden = true);

    const modem = document.getElementById('modem').value;
    const list = document.getElementById('operator_preset_' + modem);
    list.hidden = false;

    const act = document.getElementById('access_technology').value;

    for(const element of list.children) {
        element.disabled = element.hidden || act !== "all" && element.dataset.act !== act;
    }

    operator_preset_section.hidden = false;
    operator_manual_section.hidden = true;
}

function networkChange(edit) {
    let network = document.getElementById('network' + edit).checked;
    document.getElementById('network' + edit).value = (network ? 'host' : null);
}

function docker_path() {
    let docker_logger = document.getElementById('docker_logger').checked;
    document.getElementById('docker_log_path').disabled = !docker_logger;
    if (!docker_logger) {
        document.getElementById('docker_log_path').value = '';
    }
}
//endregion

//region measurement tasks

function getMeasurementList(listName) {
        let measurement_tasks = document.getElementById(listName);
        let measurement_tasks_list = [];
        for (let i = 0; i < measurement_tasks.children.length; i++) {
            //get input fields
            let task_name = measurement_tasks.children[i]?.children["task_name"]?.value;
            let task_type = measurement_tasks.children[i]?.children["task_type"]?.value;
            let image_name = measurement_tasks.children[i]?.children["image_name"]?.value;
            let environment_variables = measurement_tasks.children[i]?.children["environment_variables_value"]?.value ?? null;
            let docker_logger = measurement_tasks.children[i]?.children["docker_logger"]?.value === 'true';
            let docker_log_path = docker_logger ? measurement_tasks.children[i]?.children["docker_log_path"]?.value : null;
            let network = measurement_tasks.children[i]?.children["network"]?.value ?? null;
            let pause = measurement_tasks.children[i]?.children["pause"]?.value ?? 0;
            pause = parseInt(pause) ?? 0;
            if (pause < 0) pause = 0;

            measurement_tasks_list.push({
                'name': task_name,
                'image_name': image_name,
                'environment': (environment_variables !== null && environment_variables !== '') ? environment_variables.split(';') : null,
                'docker_logger': docker_logger,
                'docker_log_path': docker_log_path,
                'network': network,
                'pause': pause,
                'privileged': true      //todo: add privileged flag to measurement task
            });
        }
        return measurement_tasks_list;
}

removeItem = function (item, fewer_items = true) {
    const parent = item.parentElement;
    let editTaskButton = parent.querySelector(".editTaskButton");
    const taskType = editTaskButton.name;
    const id = editTaskButton.id;

    item.parentElement.parentElement.parentElement.remove();

    if (fewer_items) {
        adjustButtonIds(taskType, id);
        decrementTasksCounter(taskType);
    }
}

function getId(item) {
    const parent = item.parentElement;
    let editTaskButton = parent.querySelector(".editTaskButton");
    return parseInt(editTaskButton.id);
}

function createHiddenInput(name, value) {
    const nameEscaped = name.replaceAll("\"", "&quot;");

    let valueEscaped;

    if(typeof value === "string") {
        valueEscaped = value.replaceAll("\"", "&quot;");
    } else {
        valueEscaped = value;
    }

    return '<input type="hidden" name="' + nameEscaped + '" value="' + valueEscaped + '">';
}
let id_measurement_tasks = -1;
let id_background_tasks = -1;
let id_background_later_tasks = -1;
function createTaskItemHTML(task_name, task_type, image_name, environment_variables, docker_logger, docker_log_path, network, pause, position = null) {
    // TODO: rewrite this using <template>

    let environment_variables_html = '';
    environment_variables_html += createHiddenInput('task_name', task_name);
    environment_variables_html += createHiddenInput('task_type', task_type);
    environment_variables_html += createHiddenInput('image_name', image_name);
    environment_variables_html += createHiddenInput('docker_logger', docker_logger);
    if (environment_variables !== null && environment_variables !== undefined && environment_variables !== '') {
        environment_variables_html += createHiddenInput('environment_variables_value', environment_variables);
    }
    if (docker_log_path !== null && docker_log_path !== undefined && docker_log_path !== '' && docker_logger) {
        environment_variables_html += createHiddenInput('docker_log_path', docker_log_path);
    }
    if (network !== null && network !== undefined && network !== '') {
        environment_variables_html += createHiddenInput('network', network);
    }
    environment_variables_html += createHiddenInput('pause', pause);

    let id;
    if (position === null) {
        if (task_type === "measurement_tasks") {
            id_measurement_tasks += 1;
            id = id_measurement_tasks;
        } else if (task_type === "background_tasks") {
            id_background_tasks += 1;
            id = id_background_tasks;
        } else {
            id_background_later_tasks += 1;
            id = id_background_later_tasks;
        }
    } else {
        id = position;
    }

    return environment_variables_html +
        '<div class="card bg-light mb-3 close" style="max-width: 20rem;">' +
        '<div class="card-header">' + task_name + '<button type="button" class="btn btn-secondary" aria-label="Close" style="float: right; margin-left: 10px" onclick="removeItem(this)">'+ '<i class="bi bi-x" style="font-size: 15px"></i>' + '</button>'  + '<button name=' + task_type + ' id=' + id + ' type="button" class="btn btn-secondary editTaskButton" aria-label="Edit" style="float: right;" onclick="editJob(this.name, this.id, this)">'+ '<i class="bi bi-pencil" style="font-size: 15px"></i>' + '</button>' + '</div>' +
        '<div class="card-body">' +
        '<p class="card-text" style="font-size: 0.7rem">' +
        '<b>Image Name:</b> ' + image_name + '<br>' +
        '<b>Environment Variables:</b> ' + environment_variables + '<br>' +
        '<b>Docker Logger:</b> ' + docker_logger + '<br>' +
        '<b>Docker Log Path:</b> ' + docker_log_path + '<br>' +
        '<b>Network:</b> ' + network + '<br>' +
        '<b>Pause:</b> ' + pause + '<br>' +
        '</p>' +
        '</div>';
}

function decrementTasksCounter(openedTaskType) {
    if (openedTaskType === "measurement_tasks") {
        id_measurement_tasks -= 1;
    } else if (openedTaskType === "background_tasks") {
        id_background_tasks -= 1;
    } else {
        id_background_later_tasks -= 1;
    }
}

function adjustButtonIds(openedTaskType, openedId) {
    const editTaskButtons = document.querySelectorAll('button.editTaskButton');

    editTaskButtons.forEach(editTaskButton => {
       if (editTaskButton.name === openedTaskType && editTaskButton.id > openedId) {
           editTaskButton.id = (parseInt(editTaskButton.id) - 1).toString();
       }
    });
}

function removeEnvironmentVariables() {
    const environmentVariables = document.getElementsByName("environment_variables");
        Array.from(environmentVariables).forEach(environmentVariable => {
            if (environmentVariable.parentNode) {
                environmentVariable.parentNode.removeChild(environmentVariable);
            }
        })

    const envFieldsContainer = document.getElementById('env-fields');
    envFieldsContainer.innerHTML = "";
}

function addMeasurementTask(edit, position = null, ignore_job_distinct=false) {
    let task_name = document.getElementById('taskName' + edit).value;
    let task_type = document.getElementById('taskType' + edit).value;
    let image_name = document.getElementById('imageName' + edit).value;

    const measurement_list = getMeasurementList('measurement_tasks');
    const background_list = getMeasurementList('background_tasks');
    const background_later_list = getMeasurementList('background_later_tasks');
    const all_measurement_types_list = measurement_list.concat(background_list, background_later_list);
    if (!ignore_job_distinct) {
        let new_job_distinct = true;
        all_measurement_types_list.forEach(measurement_element => {
            if (measurement_element["name"] === task_name) {
                alert("The names for the jobs must be distinct!");
                new_job_distinct = false;
            }
        });

        if (!new_job_distinct) {
            return;
        }
    }

    const environment_variables_elements = document.getElementsByName('environment_variables');
    let environment_variables = "";
    let not_add_measurement = false;

    if (environment_variables_elements.length === 1 && environment_variables_elements[0].id === 'environment_variables') {
        environment_variables = environment_variables_elements[0].value;
        if (environment_variables !== "" && environment_variables.slice(-1) === ";") {
            environment_variables = environment_variables.slice(0,-1);
        }
    } else {
        environment_variables_elements.forEach((el => {
            let value = el.value
            if (value !== ""){
                if (el.value.includes(" ")) {
                    value = '"' + value + '"'
                }
                environment_variables += el.id + "=" + value + ";"
            } else {
                if (el.required) {
                    not_add_measurement = true;
                }
            }
        }));
        if (environment_variables.endsWith(";")) {
            environment_variables = environment_variables.slice(0, -1);
        }
    }
    if (not_add_measurement) {
        alert("Please fill out all required environment variables!");
        return;
    }
    if (image_name === 'exp-bricklet-voltage-current'){
        let tf_device = document.getElementById('tf_device').value

        if (tf_device === '' || tf_device === null || tf_device === undefined) {
            alert('Please choose a device to measure the voltage and current!');
            return;
        }

        // add device to environment variables
        if (environment_variables === null || environment_variables === undefined || environment_variables === ''){
            environment_variables = 'TF_DEVICE=' + tf_device;
        } else {
            environment_variables = environment_variables + ';TF_DEVICE=' + tf_device;
        }
    }
    let docker_logger = document.getElementById('docker_logger').checked;
    let docker_log_path = docker_logger ? document.getElementById('docker_log_path').value : null;
    let network = document.getElementById('network' + edit).checked ? document.getElementById('network').value : null;
    let pause = document.getElementById('pause' + edit).value ?? 0;

    if (task_name === '' || task_name === null || task_name === undefined
        || image_name === '' || image_name === null || image_name === undefined) {
        alert('Please enter a job name and a docker image');
        return;
    }

    if (docker_logger && docker_log_path === '') {
        alert('Please enter a docker log path or disable docker logger flag');
        return;
    }

    let measurement_tasks = document.getElementById(task_type)
    let li = document.createElement('li');
    li.className = 'list-group-item';
    //add items as hidden input fields
    li.innerHTML = createTaskItemHTML(task_name, task_type, image_name, environment_variables,
        docker_logger, docker_log_path, network, pause, position);
    if (position !== null && position < measurement_tasks.children.length) {
        measurement_tasks.children[position].before(li);
    } else {
        measurement_tasks.appendChild(li);
    }

    // clear form
    document.getElementById('taskName').value = '';
    document.getElementById('taskType').value = 'background_tasks';
    document.getElementById('imageName').value = '';
    removeEnvironmentVariables();
    document.getElementById('docker_logger').checked = false;
    document.getElementById('docker_log_path').value = null;
    document.getElementById('docker_log_path').disabled = true;
    document.getElementById('network').checked = true;
    document.getElementById('pause').value = 0;
    document.getElementById('tf_device').value = '';
    document.getElementById('tf_device_dropdown').hidden = true;
    taskTypeChange();
    return true;
}

//endregion

function importTasks(tasks, task_type, task_list, image_names) {
    for (let i = 0; i < tasks.length; i++) {
        if (tasks[i].name === null || tasks[i].name === undefined) {
            alert('Failed to import all measurement tasks: missing name');
            continue;
        }

        if (tasks[i].image_name === null || tasks[i].image_name === undefined) {
            alert('Failed to import all measurement tasks: missing image name');
            continue;
        }
        if (image_names.indexOf(tasks[i].image_name) === -1) {
            alert('Failed to import all measurement tasks: unknown image name');
            continue;
        }


        if (tasks[i].docker_logger && (tasks[i].docker_log_path === null || tasks[i].docker_log_path === undefined)) {
            alert('Failed to import all background tasks: missing docker log path');
            continue;
        }

        // check if UID or device name is set for Voltage and Current measurement
        if (
            tasks[i].image_name === 'exp-bricklet-voltage-current' && (
                tasks[i].environment === null || tasks[i].environment === undefined || tasks[i].environment === '' ||
                tasks[i].environment.filter(e => e.startsWith('UID=') || e.startsWith('TF_DEVICE=')).length <= 0
            )
        ) {
            alert('Failed to import all measurement tasks: missing environment variable UID or TF_DEVICE for Voltage and Current measurement');
            continue;
        }

        let li = document.createElement('li');
        li.className = 'list-group-item';
        //add items as hidden input fields
        li.innerHTML =
            createTaskItemHTML(
                tasks[i].name,
                task_type,
                tasks[i].image_name,
                tasks[i].environment?.join(';') ?? null,    // join environment variables with ;. Needed for import from JSON.
                tasks[i].docker_logger ?? false,
                tasks[i].docker_log_path ?? null,
                tasks[i].network ?? null,
                tasks[i].pause ?? 0
            );
        task_list.appendChild(li);
    }
}

//region json import
function importFromJsonModal() {
    const json = document.getElementById('jsonData').value;

    if (json === '' || json === null || json === undefined) {
        alert('Please enter a JSON string');
        return;
    }

    let measurement;

    try {
        measurement = JSON.parse(json);
    } catch (e) {
        alert('Please enter a valid JSON string');
        return;
    }

    if (measurement === null || measurement === undefined) {
        alert('Please enter a valid JSON string');
        return;
    }

    importFromJson(measurement);

    document.getElementById('jsonData').value = '';
    $('#jsonImporter').modal('hide');
}

function importFromJson(measurement) {
    // set measurement head
    document.getElementById('name').value = measurement.experiment_name ?? null;
    document.getElementById('modem').value = measurement.modem ?? null;
    if(measurement.modem === iot_modem){
        document.getElementById('act_config').hidden = false;
    }
    if (measurement.modem !== null && measurement.modem !== undefined) {
        document.getElementById('access_technology').disabled = false;
        modemChange(measurement.modem);
    }
    document.getElementById('access_technology').value = measurement.modem_configuration.act_mode ?? 'all';
    document.getElementById('iteration').value = measurement.repeat ?? 1;
    document.getElementById('operator_mode').value = measurement.modem_configuration.operator_mode ?? 'any';
    if (measurement.modem_configuration.operator_mode !== 'manual') {
        document.getElementById('operator').disabled = true;
    }
    document.getElementById('operator').value = measurement.modem_configuration.operators?.join(';') ?? null;

    updateOperatorPreset();

    document.getElementById('apn').value = measurement.modem_configuration.apn ?? 'em';

    document.getElementById('iptype').value = measurement.modem_configuration['ip-type'] ?? 'ipv4';
    document.getElementById('gsm_band').value = measurement.modem_configuration.gsm_band ?? null;
    document.getElementById('catm1_band').value = measurement.modem_configuration.catm1_band ?? null;
    document.getElementById('nbiot_band').value = measurement.modem_configuration.nbiot_band ?? null;
    document.getElementById('experiment_pause').value = measurement.experiment_pause ?? 0;
    document.getElementById('background_pause').value = measurement.background_tasks.pause ?? 0;

    // Scheduling options
    if(document.getElementById("date_input")) {
        if(measurement.is_scheduled_task) {
            showScheduleTask();
        } else {
            hideScheduleTask();
        }

        document.getElementById('repeat_select').value = measurement.repeat_scheduled_task ?? 'never';

        if(measurement.scheduled_task_date_time) {
            if(measurement.scheduled_task_date_time.date) document.getElementById("date_input").value = measurement.scheduled_task_date_time.date;
            if(measurement.scheduled_task_date_time.time) document.getElementById("time_input").value = measurement.scheduled_task_date_time.time;
        }

        document.getElementById('repeat_select_end').value = measurement.end_repetition_scheduled_task ?? 'never';

        if(measurement.end_repetition_scheduled_task_date_time) {
            if(measurement.end_repetition_scheduled_task_date_time.date) document.getElementById("date_input_repeat").value = measurement.end_repetition_scheduled_task_date_time.date;
            if(measurement.end_repetition_scheduled_task_date_time.time) document.getElementById("time_input_repeat").value = measurement.end_repetition_scheduled_task_date_time.time;
        }

        document.getElementById('num_repetitions_input').value = measurement.end_repetition_scheduled_task_num_repetitions ?? null;

        checkDateTimeVisible();
    }

    // set measurement body
    let measurement_tasks = measurement.measurement_tasks.tasks;
    let background_tasks = measurement.background_tasks.tasks;
    let background_later_tasks = measurement.background_later_tasks.tasks;
    let measurement_tasks_list = document.getElementById('measurement_tasks');
    let background_tasks_list = document.getElementById('background_tasks');
    let background_later_tasks_list = document.getElementById('background_later_tasks');

    // clear lists
    measurement_tasks_list.innerHTML = '';
    background_tasks_list.innerHTML = '';
    background_later_tasks_list.innerHTML = '';

    // add measurement tasks
    importTasks(measurement_tasks, "measurement_tasks", measurement_tasks_list, window.importMeasurementImages)

    // add background tasks
    importTasks(background_tasks, "background_tasks", background_tasks_list, window.importBackgroundImages)

    // add background later tasks
    importTasks(background_later_tasks, "background_later_tasks", background_later_tasks_list, window.importBackgroundLaterImages)
}
//endregion
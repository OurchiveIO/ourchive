window.addEventListener("load", function() {
    initShowMores('anthology', 'anthology-tag-container', 'anthology-description-container', 'tags', 'description');
});
function removeUser(user_id) {
    var parent = document.getElementById("anthology-form-user-"+user_id+"-parent");
    parent.remove();
}

function populateUserInput(user_id, username) {
    var parent = document.getElementById("anthology-form-users")
    var wrapper= document.createElement('div');
    wrapper.setAttribute('id', 'anthology-form-user-'+user_id+'-parent');
    wrapper.innerHTML= '<input id="anthology-form-cocreator-'+user_id+'-hidden" type="hidden" name="anthology_cocreators_'+user_id+'" value="'+user_id+'"> <p id="anthology-user-'+user_id+'-display">'+username+' <a class="link-underline link-underline-opacity-0" onclick="removeUser('+user_id+')" id="anthology-user-'+user_id+'-delete"><i class="bi bi-backspace"></i></a></p>';
    parent.appendChild(wrapper);
    document.getElementById("anthology-form-new-user").value = '';
    document.getElementById("anthology-form-new-user").focus();
    document.getElementById("anthology-find-user-dropdown").innerHTML = "";
}
function doWorkAutocomplete(term, anthology_id=0) {
  if (term.length < 2)
  {
    return;
  }
  var complete_select = 'anthology-autocomplete-dropdown';
  fetch(`/bookmark-autocomplete?text=${term}&source=edit&obj_id=${anthology_id}`)
    .then((response) => {
      return response.text();
    })
    .then((templateText) => {
        document.getElementById(complete_select).innerHTML = "";
        document.getElementById(complete_select).innerHTML = templateText;
        let dropdownElementList = [];
        dropdownElementList.push(document.getElementById(complete_select));
        const dropdownList = [...dropdownElementList].map(dropdownToggleEl => new bootstrap.Dropdown(dropdownToggleEl));
        dropdownList[0].show();
    });
}

function populateWorkInput(work_id, work_display, anthology_id=null) {
    // visible list
    var list = document.getElementById("anthology-list")
    var li = document.createElement('li');
    li.setAttribute('id', 'work-list-'+work_id);
    li.classList.add(...['work-list-item', 'list-group-item', 'sortable-item']);
    li.setAttribute('draggable', 'true');
    let fetch_url = '';
    if (anthology_id !== null && anthology_id > 0) {
        fetch_url = `/anthologies/${anthology_id}/works/render?work_id=${work_id}`;
    }
    else {
       fetch_url = `/anthologies/0/works/render?work_id=${work_id}`;
    }

    fetch(fetch_url)
        .then((response) => {
          return response.text();
        })
            .then((templateText) => {
                li.innerHTML = templateText;
                list.appendChild(li);
                document.getElementById("anthology-entry").value = '';
                document.getElementById("anthology-entry").focus();
                document.getElementById("anthology-autocomplete-dropdown").innerHTML = "";
            });
}
function removeWork(event, work_id) {
    var li = document.getElementById("works_"+work_id+"_li");
    var hidden = document.getElementById("works_"+work_id);
    li.remove();
    hidden.remove();
}

function handleModalDelete(url, anthology_id=null) {
    fetch(url)
    .then((response) => {
        let work_id = null;
        if (anthology_id !== null)
        {
            work_id = url.replace('/anthologies/'+anthology_id+'/work/', '').replace('/delete', '');
        }
        else {
            work_id = url.replace('/anthologies/1/work/', '').replace('/delete', '');
        }
        document.getElementById('work-list-'+work_id).remove();
        bootstrap.Modal.getOrCreateInstance(document.getElementById('work-anthology-'+work_id+'-modal-delete')).hide();
    });
}
document.addEventListener('DOMContentLoaded', () => {
    initializeMultiSelect('anthology-form-languages');
    initializeListReorder('anthology-list', '.anthology-tracker');
    initializeEditTags();
});
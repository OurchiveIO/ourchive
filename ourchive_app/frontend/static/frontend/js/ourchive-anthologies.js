window.addEventListener("load", function() {
    initShowMores('anthology', 'anthology-tag-container', 'anthology-description-container', 'tags', 'description');
});

function doUserAutocomplete(term) {
  if (term.length < 2)
  {
    return;
  }
  var complete_select = 'anthology-find-user-dropdown';
  fetch('/user-autocomplete?text='+term)
    .then((response) => {
      return response.text();
    })
    .then((templateText) => {
    document.getElementById(complete_select).innerHTML = "";
    document.getElementById(complete_select).innerHTML = templateText;
    UIkit.drop(document.getElementById(complete_select)).show();
    });
}

function removeUser(user_id) {
    var parent = document.getElementById("anthology-form-user-"+user_id+"-parent");
    parent.remove();
}

function populateUserInput(user_id, username) {
    // parent div
    var parent = document.getElementById("anthology-form-users")
    // user to add
    var final = username;
    var wrapper= document.createElement('div');
    wrapper.classList.add('uk-margin-small');
    wrapper.classList.add('uk-inline');
    wrapper.classList.add('uk-margin-remove-top');
    wrapper.setAttribute('id', 'anthology-form-user-'+user_id+'-parent');
    wrapper.innerHTML= '<input id="anthology-form-cocreator-'+user_id+'-hidden" type="hidden" name="anthology_cocreators_'+user_id+'" value="'+user_id+'"> <span class="uk-button-primary uk-border-rounded ourchive-tag-list uk-margin-small-right" id="anthology-user-'+user_id+'-display">'+username+' <span uk-icon="icon:ourchive-backspace;ratio:.6" onclick="removeUser('+user_id+')" id="anthology-user-'+user_id+'-delete"></span></span>';
    var input = document.getElementById("anthology-form-user-search");
    input.remove();
    parent.appendChild(wrapper);
    parent.appendChild(input);
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
    UIkit.drop(document.getElementById(complete_select)).show();
    });
}

function populateWorkInput(work_id, work_display, anthology_id=null) {
    // visible list
    var list = document.getElementById("anthology-list")
    var li = document.createElement('li');
    li.setAttribute('id', 'work-list-'+work_id);
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
      UIkit.modal(document.getElementById('work-anthology-'+work_id+'-modal-delete')).hide();
      document.getElementById('work-list-'+work_id).remove();
    });
}
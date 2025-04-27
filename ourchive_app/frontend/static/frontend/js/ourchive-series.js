function doWorkAutocomplete(term) {
  if (term.length < 2)
  {
    return;
  }
  var complete_select = 'series-autocomplete-dropdown';
  fetch('/bookmark-autocomplete?text='+term+"&source=edit")
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

function populateWorkInput(work_id, work_display, series_id=null) {
    // visible list
    var list = document.getElementById("series-list")
    var li = document.createElement('li');
    li.setAttribute('id', 'work-list-'+work_id);
    li.classList.add(...['work-list-item', 'list-group-item', 'sortable-item']);
    li.setAttribute('draggable', 'true');
    let fetch_url = '';
    if (series_id !== null) {
        fetch_url = `/series/${series_id}/works/render?work_id=${work_id}`;
    }
    else {
        fetch_url = '/series/0/works/render?work_id='+work_id;
    }
    fetch(fetch_url)
        .then((response) => {
          return response.text();
        })
            .then((templateText) => {
                li.innerHTML = templateText;
                list.appendChild(li);
                document.getElementById("series_entry").value = '';
                document.getElementById("series_entry").focus();
                document.getElementById("series-autocomplete-dropdown").innerHTML = "";
            });
}
function removeWork(event, work_id) {
    var li = document.getElementById("works_"+work_id+"_li");
    var hidden = document.getElementById("works_"+work_id);
    li.remove();
    hidden.remove();
}

function handleModalDelete(url, series_id=null) {
    fetch(url)
    .then((response) => {
        if (series_id !== null) {
             work_id = url.replace('/series/'+series_id+'/work/', '').replace('/delete', '');
        }
        else {
            work_id = url.replace('/series/1/work/', '').replace('/delete', '');
        }
      bootstrap.Modal.getOrCreateInstance(document.getElementById('work-series-'+work_id+'-modal-delete')).hide();
      document.getElementById('work-list-'+work_id).remove();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initializeListReorder('series-list', '.series-tracker');
});
document.addEventListener('DOMContentLoaded', () => {

    if (document.getElementById('work-form-languages') !== null) {
        initializeEditTags();
        initializeMultiSelect('work-form-languages');
        initializeListReorder('chapters_list', '.chapters_tracker');
    }

});

function addSelectedCollection() {
    document.querySelectorAll('.add-to-bookmark-radio').forEach(function(elm)
    {
        if (elm.checked === true) {
            var url = "{% url 'fe-add-collection-to-bookmark' work.id %}";
            window.open(url + '?collection_id=' + elm.name, '_blank');
        }
    });
}

function updateChapter(currentId, currentNumber, workId) {
    var selectedOption = document.getElementById("work-chapter-select").value.split(',');
    var href = "";
    if (selectedOption[0] === "-1") {
        href = `/works/${workId}/`
    }
    else if (selectedOption[0] === "-2") {
        href = `/works/${workId}/?view_full=true`
    }
    else {
        let offset = selectedOption[1] - 1;
        href = `/works/${workId}/${offset}`;
    }
    window.location.href = href;
}

function removeUser(user_id) {
    var parent = document.getElementById("work-form-user-"+user_id+"-parent");
    parent.remove();
}

function populateUserInput(user_id, username) {
    var parent = document.getElementById("work-form-users")
    var wrapper= document.createElement('div');
    wrapper.setAttribute('id', 'work-form-user-'+user_id+'-parent');
    wrapper.innerHTML= '<input id="work-form-cocreator-'+user_id+'-hidden" type="hidden" name="work_cocreators_'+user_id+'" value="'+user_id+'"> <p id="work-user-'+user_id+'-display">'+username+' <a class="link-underline link-underline-opacity-0" onclick="removeUser('+user_id+')" id="work-user-'+user_id+'-delete"><i class="bi bi-backspace"></i></a></p>';
    parent.appendChild(wrapper);
    document.getElementById("work-form-new-user").value = '';
    document.getElementById("work-form-new-user").focus();
    document.getElementById("work-find-user-dropdown").innerHTML = "";
}
function doSeriesAutocomplete(term) {
  if (term.length < 2)
  {
    return;
  }
  var complete_select = 'work-series-dropdown';
  fetch('/series-autocomplete?text='+term)
    .then((response) => {
      return response.text();
    })
    .then((templateText) => {
    document.getElementById(complete_select).innerHTML = "";
    document.getElementById(complete_select).innerHTML = templateText;
    new bootstrap.Dropdown(document.getElementById(complete_select)).show();
    });
}

function removeSeries(series_id) {
    let parent = document.getElementById("work-form-series-existing-container");
    if (parent !== null) {
        parent.innerHTML = '';
    }
}

function populateSeriesInput(title, series_id) {
    if (!title) {
        return;
    }
    if (series_id === null) {
        series_id = title;
    }
    removeSeries(null);
    // parent div
    var parent = document.getElementById("work-form-series-existing-container");
    parent.innerHTML= '<input id="work-form-series-hidden" type="hidden" name="series_id" value="'+series_id+'"> <span class="badge text-bg-primary" id="work_series_display">'+title+' <a onclick="removeSeries('+series_id+')" id="work_series_delete"></a><i class="bi bi-x"></i></span>';
    document.getElementById("work-form-series").value = '';
    document.getElementById("work-form-series").focus();
    document.getElementById("work-series-dropdown").innerHTML = "";
}
function addSeries(event) {
    let val = document.getElementById("work-form-series").value;
    if (!val) {
        return;
    }
    populateSeriesInput(val, null);
}
function seriesCheck (e) {
    if (e.keyCode == 188 || e.keyCode == 13) {
        addSeries(e);
    }
}

function getCurrentTab(submitted) {
    var new_chapter_clicked = submitted === "New Chapter";
    document.getElementById('redirect_toc').value = new_chapter_clicked;
    getRichText(['summary', 'notes']);
    getChapterRichTextValues();
}
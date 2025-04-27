window.addEventListener('DOMContentLoaded', function() {
    initializeMultiSelect('bkcol-form-languages');
    initializeEditTags();
});


function loadMoreComments(next, chapterId, obj_id) {
    fetch(next)
      .then((response) => {
        return response.text();
      })
      .then((myText) => {
        document.getElementById(`collection-${obj_id}-comments-child-container`).innerHTML = "";
        document.getElementById(`collection-${obj_id}-comments-child-container`).innerHTML = myText;
        document.getElementById(`collection-${obj_id}-comments-child-container`).scrollIntoView();
      });
}

function doWorkAutocomplete(term) {
  if (term.length < 2)
  {
    return;
  }
  var complete_select = 'bookmark-autocomplete-dropdown';
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

function populateWorkInput(bookmark_id, bookmark_display, obj_id=null) {
    // visible list
    var list = document.getElementById("bookmarks_readonly_list")
    var wrapper= document.createElement('p');
    wrapper.innerHTML= '<input data-testid="workidstoadd-hidden" type="hidden" id="works_'+bookmark_id+'" name="workidstoadd_'+bookmark_id+'" value="workidstoadd_'+bookmark_id+'">';
    var div = wrapper.firstChild;
    list.appendChild(div);
    var li = document.createElement('li');
    li.setAttribute('id', 'works_'+bookmark_id+'_li');
    li.setAttribute("data-testid", "workidstoadd")
    li.classList.add("list-group-item");
    li.innerHTML = bookmark_display+' (<a class="link-underline link-underline-opacity-0 link-underline-opacity-25-hover" onclick="removeWork(event,'+bookmark_id+')">Remove</a>)';
    list.appendChild(li);
    document.getElementById("bookmark_entry").value = '';
    document.getElementById("bookmark_entry").focus();
    document.getElementById("bookmark-autocomplete-dropdown").innerHTML = "";
}
function removeWork(event, bookmark_id) {
    var li = document.getElementById("works_"+bookmark_id+"_li");
    var hidden = document.getElementById("works_"+bookmark_id);
    li.remove();
    hidden.remove();
}

function addSelectedWorks() {
    var bookmarks = document.querySelectorAll('.add-to-collection-checkbox');
    bookmarks.forEach((bookmark) => {
        if (bookmark.checked) {
            var bookmark_display = document.getElementById("bookmark-"+bookmark.name+"-bookmark").innerHTML;
            populateWorkInput(bookmark.name, bookmark_display);
        }
    });
}

function removeUser(user_id) {
    var parent = document.getElementById("collection-form-user-"+user_id+"-parent");
    parent.remove();
}

function populateUserInput(user_id, username) {
    // parent div
    var parent = document.getElementById("collection-form-users")
    // user to add
    var final = username;
    var wrapper= document.createElement('div');
    wrapper.setAttribute('id', 'collection-form-user-'+user_id+'-parent');
    wrapper.innerHTML= '<input id="bkcol-form-cocreator-'+user_id+'-hidden" type="hidden" name="collection_cocreators_'+user_id+'" value="'+user_id+'"> <p id="collection_user_'+user_id+'_display">'+username+' <a class="link-underline link-underline-opacity-0" onclick="removeUser('+user_id+')" id="collection_user_'+user_id+'_delete"><i class="bi bi-backspace"></i></a></p>';
    parent.appendChild(wrapper);
    document.getElementById("collection_form_new_user").value = '';
    document.getElementById("collection_form_new_user").focus();
    document.getElementById("collection-find-user-dropdown").innerHTML = "";
}
window.addEventListener("load", function() {
    initShowMores('collection', 'collection-tag-container', 'collection-description-container', 'tags', 'description');
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
    UIkit.drop(document.getElementById(complete_select)).show();
    });
}

function populateWorkInput(bookmark_id, bookmark_display, obj_id=null) {
    // visible list
    var list = document.getElementById("bookmarks_readonly_list")
    // bookmark to add
    var final = bookmark_display;
    var wrapper= document.createElement('div');
    wrapper.innerHTML= '<input type="hidden" id="works_'+bookmark_id+'" name="workidstoadd_'+bookmark_id+'" value="workidstoadd_'+bookmark_id+'">';
    var div = wrapper.firstChild;
    list.appendChild(div);
    var li = document.createElement('li');
    li.setAttribute('id', 'works_'+bookmark_id+'_li');
    li.innerHTML = bookmark_display+' (<a onclick="removeWork(event,'+bookmark_id+')">Remove</a>)';
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
            console.log(bookmark);
            var bookmark_display = document.getElementById("bookmark-"+bookmark.name+"-bookmark").innerHTML;
            populateWorkInput(bookmark.name, bookmark_display);
        }
    });
}

// multi-user functionality
function doUserAutocomplete(term) {
  if (term.length < 2)
  {
    return;
  }
  var complete_select = 'collection-find-user-dropdown';
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
    var parent = document.getElementById("collection-form-user-"+user_id+"-parent");
    parent.remove();
}

function populateUserInput(user_id, username) {
    // parent div
    var parent = document.getElementById("collection-form-users")
    // user to add
    var final = username;
    var wrapper= document.createElement('div');
    wrapper.classList.add('uk-margin-small');
    wrapper.classList.add('uk-inline');
    wrapper.classList.add('uk-margin-remove-top');
    wrapper.setAttribute('id', 'collection-form-user-'+user_id+'-parent');
    wrapper.innerHTML= '<input id="bkcol-form-cocreator-'+user_id+'-hidden" type="hidden" name="collection_cocreators_'+user_id+'" value="'+user_id+'"> <span class="uk-button-primary uk-border-rounded ourchive-tag-list uk-margin-small-right" id="collection_user_'+user_id+'_display">'+username+' <span uk-icon="icon:ourchive-backspace;ratio:.6" onclick="removeUser('+user_id+')" id="collection_user_'+user_id+'_delete"></span></span>';
    var input = document.getElementById("collection-form-user-search");
    input.remove();
    parent.appendChild(wrapper);
    parent.appendChild(input);
    document.getElementById("collection_form_new_user").value = '';
    document.getElementById("collection_form_new_user").focus();
    document.getElementById("collection-find-user-dropdown").innerHTML = "";
}
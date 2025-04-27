function removeFile(object, replace_selector, object_type) {
	document.getElementById(object+'-file-input').value = "";
	document.getElementById(object+'-file-uk-input').value = "";
    document.getElementById(object+'-file-uk-input-original').value = "";
    if (object_type.includes('img')) {
        document.getElementById(replace_selector).src = '';
        document.getElementById(`${replace_selector}-toggle`).classList.add('disabled');
        if (document.getElementById(`${replace_selector}-inline`).classList.contains('show')) {
            document.getElementById(`${replace_selector}-inline`).classList.remove('show');
        }
    }
}

function resetFile(objectName) {
    document.getElementById(`${ objectName }-file-input`).disabled = false;
    document.getElementById(`${ objectName }-file-input`).value = null;
}

function ourchiveUpload(value, object, object_type, upload_url, replace_selector) {
    if (value.target === undefined) {
        return;
    }

    // Create a new FormData instance
    let data = new FormData();

    // Create a XMLHTTPRequest instance
    let request = new XMLHttpRequest();
    document.getElementById(`${ object }-file-input`).disabled = true;

    // Set the response type
    request.responseType = "json";

    // Get a reference to the file
    let file = value.target.files[0];

    // Get a reference to the filename
    let filename = file.name;

    // Append the file to the FormData instance
    data.append("file", file);

    // request progress handler
    request.upload.addEventListener("progress", function (e) {
        // Get the loaded amount and total filesize (bytes)
        let loaded = e.loaded;
        let total = e.total

        // Calculate percent uploaded
        let percent_complete = (loaded / total) * 100;

        // Update the progress text and progress bar
        document.getElementById(`${ object }-progressbar-${ object_type }`).setAttribute("style", `width: ${Math.floor(percent_complete)}%`);
        document.getElementById(`${ object }-progressbar-${ object_type }`).innerText = `${Math.floor(percent_complete)}%`;

      })

      // request load handler (transfer complete)
      request.addEventListener("load", function (e) {
        if (request.status === 200) {
            document.getElementById(`${ object }-progressbar-${ object_type }`).setAttribute("style", `width: 100%`);
            document.getElementById(`${ object }-progressbar-${ object_type }`).innerText = `100%`;
            let result = request.response.final_url;
            document.getElementById(`${ object }-file-uk-input`).value = result;
            document.getElementById(`${ object }-file-uk-input-original`).value = result;
            if (object_type.includes('img')) {
                document.getElementById(replace_selector).src = result;
                document.getElementById(`${replace_selector}-toggle`).classList.remove('disabled');
            }
            else if (document.getElementById(replace_selector) !== null) {
                document.getElementById(replace_selector).style.visibility = "hidden";
            }
        }
        else {
            document.getElementById(`${ object }-progressbar-${ object_type }`).setAttribute("style", `width: 0%`);
            document.getElementById(`${ object }-progressbar-${ object_type }`).innerText = `0%`;
            document.getElementById(`${ object }-file-input`).value = null;
        }
        document.getElementById(`${ object }-file-input`).disabled = false;
      });

      // request error handler
      request.addEventListener("error", function (e) {
          console.log('error', arguments);
          var result = JSON.parse(arguments[0].xhr.response)['message'];
          const toastBootstrap = bootstrap.Toast.getOrCreateInstance(document.getElementById("uploadFailedToast"));
          toastBootstrap.show();
      });

      // request abort handler
      request.addEventListener("abort", function (e) {
        resetFile();
      });

      // Open and send the request
      request.open("post", upload_url);
      request.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
      request.send(data);

      document.getElementById(`${ object }-file-cancel`).addEventListener("click", function () {
        request.abort();
      });
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        cookies.forEach(function (value) { 
            var cookie = value.trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                return;
            }
        });
    }
    return cookieValue;
}

function removeItem(arr, value) {
  const index = arr.indexOf(value);
  
  if (index > -1) {
    arr.splice(index, 1);
  }
  
  return arr;
}


function setSearchToggles(groupName, mobile=false) {
    var activeTabs = localStorage.getItem('ourchive-active-tabs');
    var itemId = 'accordion-item-'+groupName;
    if (mobile) {
        itemId = itemId + '-mobile';
    }
    var accordionItem = document.getElementById(itemId);
    var open = !accordionItem.classList.contains('uk-open');
    if (open === true) {
        if (activeTabs !== null) {
            var activeTabs = activeTabs.split(',');
            if (activeTabs.includes(groupName.toString())) {
                return;
            }
            else {
                activeTabs.push(groupName);
            }
            activeTabs = activeTabs.join(',');
        }
        else {
            activeTabs = groupName;
        }
        localStorage.setItem('ourchive-active-tabs', activeTabs);
    }
    else {
        if (activeTabs !== null) {
            var activeTabs = activeTabs.split(',');
            if (activeTabs.includes(groupName.toString())) {
                activeTabs = removeItem(activeTabs, groupName.toString());
            }
            if (activeTabs.length > 0) {
                activeTabs = activeTabs.join(',');
                localStorage.setItem('ourchive-active-tabs', activeTabs);
            }
            else {
                localStorage.removeItem('ourchive-active-tabs');
            }
        }
    }
}

function addWorkType(element, id, typeName) {
    if (element.checked === true) {
        const hidden = document.createElement("option");
        hidden.setAttribute("id", `work-type-${id}`);
        hidden.setAttribute("name", `work-type-${id}`);
        hidden.setAttribute("value", typeName);
        hidden.selected = true;
        hidden.innerText = typeName;
        document.getElementById(`work_types[]`).append(hidden);
    }
    else {
        document.getElementById(`work-type-${id}`).remove();
    }
}

function doLanguageAutocomplete(term, source, selector='', clickAction='') {
  if (term.length < 2)
  {
    return;
  }
  let complete_select = `language-autocomplete-dropdown${selector}`;
  fetch('/language-autocomplete?text='+term+"&source="+source+"&click_action="+clickAction)
    .then((response) => {
      return response.text();
    })
    .then((templateText) => {
    document.getElementById(complete_select).innerHTML = "";
    document.getElementById(complete_select).innerHTML = templateText;
    UIkit.drop(document.getElementById(complete_select)).show();
    });
}

function removeElement(include_exclude, tag) {
    document.getElementById(`${include_exclude}-wrapper-${tag}`).remove();
    document.getElementById(`${include_exclude}-${tag}-option`).selected = false;
}
function populateSavedSearch(element, includeLabel) {
    let tag = element.querySelectorAll('span')[0].innerText;
    if (document.getElementById(`${includeLabel}-wrapper-${tag}`) !== null) {
        return;
    }
    let search = document.getElementById(`${includeLabel}-wrapper`).querySelector(`.${includeLabel}-search-wrapper`);
    const tagWrapper = document.createElement("div");
    tagWrapper.classList.add("selected-wrapper");
    tagWrapper.setAttribute("id", `${includeLabel}-wrapper-${tag}`);
    const tagWrapperSpan = document.createElement("span");
    tagWrapperSpan.classList.add("selected-label");
    tagWrapperSpan.innerText = tag;
    const close = document.createElement("a");
    close.classList.add("selected-close");
    close.setAttribute("tabindex", "-1");
    close.setAttribute("data-option", tag);
    close.setAttribute("data-hits", 0);
    close.setAttribute("uk-icon", "icon: ourchive-close; ratio: .75");
    close.addEventListener("click", function() {
        document.getElementById(`${includeLabel}-wrapper-${tag}`).remove();
        document.getElementById(`${includeLabel}-${tag}-option`).remove();
    });
    tagWrapper.appendChild(tagWrapperSpan);
    tagWrapper.appendChild(close);
    const hidden = document.createElement("option");
    hidden.setAttribute("id", `${includeLabel}-${tag}-option`);
    hidden.setAttribute("name", `${includeLabel}-${tag}`);
    hidden.setAttribute("value", tag);
    hidden.selected = true;
    hidden.innerText = tag;
    document.getElementById(`${includeLabel}-wrapper`).insertBefore(tagWrapper, search);
    document.getElementById(`${includeLabel}_facets[]`).appendChild(hidden);
    document.getElementById(`${includeLabel}-tag-search`).value = "";
    UIkit.drop(document.getElementById(`tag-autocomplete-dropdown-savedsearch${includeLabel}`)).hide();
    document.getElementById(`tag-autocomplete-dropdown-savedsearch${includeLabel}`).innerHTML = "";
}
function populateSavedSearchExclude(element) {
    populateSavedSearch(element, 'exclude');
}
function populateSavedSearchInclude(element) {
    populateSavedSearch(element, 'include');
}

function populateSavedSearchLanguage(element) {
    let language = element.querySelectorAll('span')[0].innerHTML;
    let search = document.getElementById(`languages-wrapper`).querySelector(`.language-search-wrapper`);
    const tagWrapper = document.createElement("div");
    tagWrapper.classList.add("selected-wrapper");
    tagWrapper.setAttribute("id", `language-wrapper-${language}`);
    const tagWrapperSpan = document.createElement("span");
    tagWrapperSpan.classList.add("selected-label");
    tagWrapperSpan.innerText = language;
    const close = document.createElement("a");
    close.classList.add("selected-close");
    close.setAttribute("tabindex", "-1");
    close.setAttribute("data-option", language);
    close.setAttribute("data-hits", 0);
    close.setAttribute("uk-icon", "icon: ourchive-close; ratio: .75");
    close.addEventListener("click", function() {
        document.getElementById(`language-wrapper-${language}`).remove()
    });
    tagWrapper.appendChild(tagWrapperSpan);
    tagWrapper.appendChild(close);
    const hidden = document.createElement("option");
    hidden.setAttribute("id", `language-${language}`);
    hidden.setAttribute("name", `language-${language}`);
    hidden.setAttribute("value", language);
    hidden.selected = true;
    hidden.innerText = language;
    document.getElementById(`languages-wrapper`).insertBefore(tagWrapper, search);
    document.getElementById(`saved-search-languages`).appendChild(hidden);
    document.getElementById(`language-search`).value = "";
    UIkit.drop(document.getElementById(`language-autocomplete-dropdown`)).hide();
    document.getElementById(`language-autocomplete-dropdown`).innerHTML = "";
}

function toggleChiveData(chive_id, selector, objType='chive', showMoreText='Show more...', hideText='Hide') {
    let overflow = document.getElementById(`show-${selector}-`+chive_id).style.overflow;
    let element_id = `show-${selector}-` + chive_id;
    let button_id = `more-btn-${selector}-` + chive_id;
    if (overflow === 'hidden' || overflow.length < 1) {
        document.getElementById(element_id).style.overflow = 'clip';
        document.getElementById(element_id).style.maxHeight = '2000px';
        document.getElementById(element_id).style.height = 'auto';
        document.getElementById(button_id).innerText = hideText;
    }
    else {
        document.getElementById(element_id).style.overflow = 'hidden';
        document.getElementById(element_id).style.maxHeight = '150px';
        document.getElementById(element_id).style.height = '150px';
        document.getElementById(button_id).innerText = showMoreText;
        document.getElementById(`${objType}-${chive_id}-tile-card`).scrollIntoView();
    }
}

function initShowMores(objType='chive', firstContainer='tag-container', secondContainer='summary-container', firstSelector='tags', secondSelector='summary') {
    [...document.getElementsByClassName(firstContainer)].forEach(el => {
        let id = el.id.replace(`show-${firstSelector}-`, '');
        let couldFit = (el.scrollHeight + document.getElementById(`show-${secondSelector}-${id}`).scrollHeight) < document.getElementById(`${objType}-${id}-tile-container`).scrollHeight;
        if (el.offsetHeight < el.scrollHeight) {
            if (!couldFit) {
                var showMore = document.getElementById(`more-btn-${firstSelector}-${id}`);
                if (showMore !== null)
                {
                    showMore.style.display = 'inline';
                }
            } else {
                el.style.height = `${el.scrollHeight}px`;
                el.style.maxHeight = `${el.scrollHeight}px`;
            }
        }
    });
    [...document.getElementsByClassName(secondContainer)].forEach(el => {
        if (el.offsetHeight < el.scrollHeight) {
            let id = el.id.replace(`show-${secondSelector}-`, '');
            document.getElementById(`more-btn-${secondSelector}-` + id).style.display = 'inline';
        }
    });
}

function goToUrl(url) {
    window.location.href = url;
}

function doUserAutocomplete(term, select_id) {
  if (term.length < 2)
  {
    return;
  }
  fetch('/user-autocomplete?text='+term)
    .then((response) => {
      return response.text();
    })
    .then((templateText) => {
    document.getElementById(select_id).innerHTML = "";
    document.getElementById(select_id).innerHTML = templateText;
    new bootstrap.Dropdown(document.getElementById(select_id)).show();
    });
}

function initializeEditTags() {
    let tagElements = document.getElementsByClassName('oc-searchable-tags');
    for (const tagElement of tagElements) {
        const tag_choices = new Choices(tagElement, {
            searchEnabled: true,
            searchChoices: true,
            removeItemButton: true,
            loadingText: 'Loading...',
        });

        tag_choices.passedElement.element.addEventListener('search', function (event) {
            let searchValue = event.detail.value;
            if (searchValue.length < 3) return;
            let source = 'edit';
            let tagType = tagElement.getAttribute("data-tag-type");
            fetch(`/tag-autocomplete?text=${searchValue}&source=${source}&type=${tagType}&fetch_all=true`)
                .then((response) => {
                  response.json().then((data) => {
                      let result = [];
                      data.tags.forEach(tag => {
                          result.push({value: tag.display_text, label: tag.display_text});
                      })
                      if (result.length > 0) {
                          tag_choices.setChoices(result, 'value', 'label', true);
                      }
                      else {
                          tag_choices.setChoices([
                              {value: searchValue, label: searchValue}
                          ], 'value', 'label', true);
                      }
                  });
                });
        });
    }
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll
        ('.sortable-item:not(.dragging)')];
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function initializeListReorder(listSelector, trackerSelector) {
    const list = document.querySelector('.sortable-list');
    let draggingItem = null;
    list.addEventListener('dragstart', (e) => {
        draggingItem = e.target;
        e.target.classList.add('dragging');
    });
    list.addEventListener('dragend', (e) => {
        e.target.classList.remove('dragging');
        document.querySelectorAll('.sortable-item')
            .forEach(item => item.classList.remove('over'));
        draggingItem = null;
        var list = document.getElementById(listSelector).getElementsByTagName("li");
        var tracking = 1;
        for (let item of list) {
            var child = item.querySelector(trackerSelector)
            child.value = tracking;
            tracking += 1;
        }
    });
    list.addEventListener('dragover', (e) => {
        e.preventDefault();
        const draggingOverItem = getDragAfterElement(list, e.clientY);
        document.querySelectorAll('.sortable-item').forEach
            (item => item.classList.remove('over'));
        if (draggingOverItem) {
            draggingOverItem.classList.add('over');
            list.insertBefore(draggingItem, draggingOverItem);
        } else {
            list.appendChild(draggingItem);
        }
    });
}

function initializeMultiSelect(selectId) {
    const select_element = document.getElementById(selectId);
    const select_choices = new Choices(select_element, { removeItemButton: true});
}
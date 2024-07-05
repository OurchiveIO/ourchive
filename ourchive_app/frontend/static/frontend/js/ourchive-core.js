function removeFile(object) {
	document.getElementById(object+'-file-input').value = "";
	document.getElementById(object+'-file-uk-input').value = "";
	console.log(document.getElementById(object+'-file-uk-input-original'));
	document.getElementById(object+'-file-uk-input-original').value = "";
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
    let tag = element.querySelectorAll('span')[0].innerHTML;
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
        document.getElementById(`${includeLabel}-wrapper-${tag}`).remove()
    });
    tagWrapper.appendChild(tagWrapperSpan);
    tagWrapper.appendChild(close);
    const hidden = document.createElement("option");
    hidden.setAttribute("id", `${includeLabel}-${tag}`);
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
                console.log(`more-btn-${firstSelector}-${id}`);
                document.getElementById(`more-btn-${firstSelector}-${id}`).style.display = 'inline';
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
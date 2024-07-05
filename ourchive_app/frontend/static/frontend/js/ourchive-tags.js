function removetag(tag, type, divider) {
    document.getElementById("tags"+divider+tag+divider+type).remove();
    document.getElementById("tags"+divider+tag+divider+type+divider+"txt").remove();
}

function sanitize(string) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        "/": '&#x2F;',
    };
    const reg = /[&<>"'/]/ig;
    return string.replace(reg, (match)=>(map[match]));
}

function tagCheck (e, type, bypass_check=false, divider='$!$') {
    if (e.keyCode == 188 || e.keyCode == 13 || bypass_check) {
        var randomId = Math.floor(Math.random() * 100) + 1
        var section = document.getElementById(type+"_tags");
        var final = document.getElementById(type+"_new_tag");
        final.value = sanitize(final.value.replace(/,\s*$/, ""));
        unescaped = final.value.replace(/,\s*$/, "");
        var wrapper= document.createElement('div');
        wrapper.innerHTML= '<input type="hidden" id="tags'+divider+randomId+divider+type+'" name="tags'+divider+final.value+divider+type+'" value="tags'+divider+final.value+divider+type+'">';
        var div= wrapper.firstChild;
        section.appendChild(div);
        wrapper.innerHTML = '<div class="uk-margin-small uk-inline"><span class="uk-button-primary uk-border-rounded ourchive-tag-list uk-margin-small-right" id="tags'+divider+randomId+divider+type+divider+'txt"><span class="uk-button-primary uk-border-rounded ourchive-tag-list">'+unescaped+' </span><span uk-icon="close" onclick="removetag(\''+randomId+'\', \''+type+'\', \''+divider+'\')" id="tags'+divider+randomId+divider+type+'_delete"></span></span></div>';
        div = wrapper.firstChild;
        section.appendChild(div);
        final.value = '';
        final.focus();
        document.getElementById('tag-autocomplete-dropdown-'+type).innerHTML = "";
        document.getElementById('no-tag-prompt-'+type).style.display = "none";
    }
}

function doAutocomplete(term, source, selector, tag_type='', divider='$!$', clickAction='') {
  if (term.length < 2)
  {
    return;
  }
  var complete_select = 'tag-autocomplete-dropdown-'+selector;
  fetch('/tag-autocomplete?text='+term+"&source="+source+"&type="+tag_type+"&click_action="+clickAction)
    .then((response) => {
      return response.text();
    })
    .then((templateText) => {      
    document.getElementById(complete_select).innerHTML = "";
    document.getElementById(complete_select).innerHTML = templateText;
    UIkit.drop(document.getElementById(complete_select)).show();
    });
}

function updateIndexSearchText(term, inForm=false) {
    if (inForm === true) {
        document.querySelectorAll('#nav-search-input').forEach(el => {
            el.value = term;
        });
    }
    else {
        document.getElementById("filter-search-text").value = term;
    }
}

function doIndexAutocomplete(term, source, selector, tag_type='', divider='$!$', clickAction='') {
    updateIndexSearchText(term, true);
    document.getElementById("filter-search-text").value = term;
    doAutocomplete(term, source, selector, tag_type, divider, clickAction);
}

function doAdminAutocomplete(term, source, selector, tag_type='', divider='$!$') {
  var complete_select = 'tag-autocomplete-dropdown-'+selector
  fetch('/tag-autocomplete?text='+term+"&source="+source+"&type="+tag_type+"&fetch_all=true")
    .then((response) => {
      return response.text();
    })
    .then((templateText) => {      
    document.getElementById(complete_select).innerHTML = "";
    document.getElementById(complete_select).innerHTML = templateText;
    UIkit.drop(document.getElementById(complete_select)).show();
    });
}

function populateTagInput(tag, tag_type, fetch_all=false, divider='$!$') {
    //tag = sanitize(tag);
    document.getElementById(tag_type+"_new_tag").value = tag;
    var evt = new CustomEvent('keyup');
    evt.which = 13;
    evt.keyCode = 13;
    if (fetch_all == "true") {
      tagCheck(evt, tag_type, true);
    }
    else {
      document.getElementById(tag_type+"_new_tag").dispatchEvent(evt);
    }
}
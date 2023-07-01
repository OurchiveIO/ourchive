function removetag(tag, type) {
    document.getElementById("tags_"+tag+"_"+type).remove();
    document.getElementById("tags_"+tag+"_"+type+"_txt").remove();
}

function tagCheck (e, type, bypass_check=false) {
    if (e.keyCode == 188 || e.keyCode == 13 || bypass_check) {
        var section = document.getElementById(type+"_tags");
        var final = document.getElementById(type+"_new_tag");
        final.value = final.value.replace(/,\s*$/, "");
        var wrapper= document.createElement('div');
        wrapper.innerHTML= '<input type="hidden" id="tags_'+final.value+'_'+type+'" name="tags_'+final.value+'_'+type+'" value="tags_'+final.value+'_'+type+'">';
        var div= wrapper.firstChild;
        section.appendChild(div);
        wrapper.innerHTML = '<span class="uk-badge uk-padding-small uk-margin-right" id="tags_'+final.value+'_'+type+'_txt"><span class="uk-text-bold uk-text-default uk-padding-small">'+final.value+' </span><span uk-icon="close" onclick="removetag(\''+final.value+'\', \''+type+'\')" id="tags_'+final.value+'_'+type+'_delete"></span></span>  ';
        div = wrapper.firstChild;
        section.appendChild(div);
        final.value = '';
        final.focus();
        document.getElementById('tag-autocomplete-dropdown-'+type).innerHTML = "";
        document.getElementById('no-tag-prompt-'+type).style.display = "none";
    }
}

function doAutocomplete(term, source, selector, tag_type='') {
  if (term.length < 5)
  {
    return;
  }
  var complete_select = 'tag-autocomplete-dropdown-'+selector;
  fetch('/tag-autocomplete?text='+term+"&source="+source+"&type="+tag_type)
    .then((response) => {
      return response.text();
    })
    .then((templateText) => {      
    document.getElementById(complete_select).innerHTML = "";
    document.getElementById(complete_select).innerHTML = templateText;
    UIkit.drop(document.getElementById(complete_select)).show();
    });
}

function doAdminAutocomplete(term, source, selector, tag_type='') {
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

function populateTagInput(tag, tag_type, fetch_all=false) {
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
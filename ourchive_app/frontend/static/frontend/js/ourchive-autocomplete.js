function doAutocomplete(term, source, selector, tag_type='') {
	var complete_select = 'tag-autocomplete-dropdown-'+selector
	if (term.length < 3)
	{
		return;
	}
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

function populateTagInput(tag, tag_type) {
	document.getElementById(tag_type+"_new_tag").value = tag;
	var evt = new CustomEvent('keyup');
	evt.which = 13;
	evt.keyCode = 13;
	document.getElementById(tag_type+"_new_tag").dispatchEvent(evt);
}
window.addEventListener("load", function(){
	  	if (localStorage.getItem('ourchive-show-filters') == null) {
	  		localStorage.setItem('ourchive-show-filters', '1');
		}
		if (localStorage.getItem('ourchive-show-filters') === '0') {
			//UIkit.toggle(document.getElementById('search-results-toggle-button')).toggle();
		}

		const checkboxes = document.querySelectorAll("input[type='checkbox']:checked");
		checkboxes.forEach(function(checkbox) {
			let checkbox_id = checkbox.getAttribute("id").replace(',mobile', '');
			if (document.getElementById(checkbox_id+"_badge") !== null) {
	            return;
	        }
			//createToken(document.getElementById("selected-filters-list"), checkbox.parentNode.innerText, checkbox.parentNode.innerText, checkbox_id+"_badge");
		});

		const inputboxes = document.querySelectorAll(".facet-val-input");
		inputboxes.forEach(function(inputbox) {
			let input_id = inputbox.getAttribute("id").replace(',mobile', '');
			if (document.getElementById(input_id+"_badge") !== null) {
	            return;
	        }
			if (inputbox.value.trim() !== "") {
				let labelParts = inputbox.id.split(',');
			    let label = labelParts[1] + ": " + inputbox.value;
			    //createToken(document.getElementById("selected-filters-list"), label, label, input_id+"_badge");
			}
		});
	});
function updateFilterToggle() {
    var showFilters = localStorage.getItem('ourchive-show-filters');
    showFilters = showFilters === '1' ? '0' : '1';
    localStorage.setItem('ourchive-show-filters', showFilters);
}
function getFormVals(event) {
    event.preventDefault();
    link = event.target.href;
    var vals_form = document.forms["searchResultsForm_work"];
    vals_form.action = link;
    document.forms["searchResultsForm_work"].submit();
}

function updateActiveTab(index) {
    document.getElementById("active_tab").value = index;
}

function toggleAnyAll(include_exclude, flyover) {
    var all_toggle_label = include_exclude + "-all-toggle-label";
    var any_toggle_label = include_exclude + "-any-toggle-label";
    if (flyover != null) {
        all_toggle_label = all_toggle_label + "-flyover";
        any_toggle_label = any_toggle_label + "-flyover";
    }
    var toggle = document.getElementById(any_toggle_label).style.visibility;
    if (toggle === "hidden") {
        document.getElementById(any_toggle_label).style.visibility = "visible";
        document.getElementById(all_toggle_label).style.visibility = "hidden";
    }
    else {
        document.getElementById(any_toggle_label).style.visibility = "hidden";
        document.getElementById(all_toggle_label).style.visibility = "visible";
    }
}

function updateSortOrder(selected, mobile) {
    if (mobile === true) {
        document.getElementById("search-results-sort-select-hidden-mobile").value = selected;
        document.forms["searchResultsForm_work_mobile"].submit();
    }
    else {
        document.getElementById("search-results-sort-select-hidden").value = selected;
        document.forms["searchResultsForm_work"].submit();
    }
}

function clearAll() {
    const options = document.querySelectorAll("option");
    options.forEach(function(option) {
        option.removeAttribute("selected");
    });
    const checkboxes = document.querySelectorAll("input[type='checkbox']");
    checkboxes.forEach(function(checkbox) {
        checkbox.checked = false;
    });
    const inputboxes = document.querySelectorAll(".facet-val-input");
    inputboxes.forEach(function(inputbox) {
        inputbox.value = "";
    });
    const filterList = document.querySelectorAll("div.selected-wrapper");
    filterList.forEach(function(element) {
        element.remove();
    });
}

function handleFacetCheckUncheck(e) {

}
function handleFacetInput(e) {

}

function searchWorks(number, term, tag_id, attr_id, work_type_id, page_params) {
    if (tag_id < 1) {
        tag_id = '';
    }
    else {
        tag_id = `&tag_id=${tag_id}`;
    }
    if (attr_id < 1) {
        attr_id = '';
    }
    else {
        attr_id = `&attr_id=${attr_id}`;
    }
    if (work_type_id < 1) {
        work_type_id = '';
    }
    else {
        work_type_id = `&work_type_id=${work_type_id}`;
    }
    if (term === 'None') {
        term = ''
    }
    else
    {
        term = `&term=${term}`;
    }
    let search_form = document.getElementById("search-results-work-facet-form");
    search_form.action = `/search/?page=${number}${term}${tag_id}${attr_id}${work_type_id}${page_params}`;
    document.getElementById("search-results-work-facet-form").submit();
}
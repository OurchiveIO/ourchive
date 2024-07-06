// Adapted from https://codepen.io/vdhug/pen/xxbPoJe

// Initialize function, create initial tokens with itens that are already selected by the user
function init(element) {
    // Create div that wraps all the elements inside (select, elements selected, search div) to put select inside
    const wrapper = document.createElement("div");
    wrapper.addEventListener("click", clickOnWrapper);
    wrapper.classList.add("multi-select-component");

    // Create elements of search
    const search_div = document.createElement("div");
    search_div.classList.add("search-container");
    const input = document.createElement("input");
    input.classList.add("selected-input");
    input.setAttribute("autocomplete", "off");
    input.setAttribute("tabindex", "0");
    input.addEventListener("keyup", inputChange);
    input.addEventListener("keydown", deletePressed);
    input.addEventListener("click", openOptions);

    const dropdown_icon = document.createElement("a");
    dropdown_icon.classList.add("dropdown-icon");

    dropdown_icon.addEventListener("click", clickDropdown);
    const autocomplete_list = document.createElement("ul");
    autocomplete_list.classList.add("autocomplete-list")
    search_div.appendChild(input);
    search_div.appendChild(autocomplete_list);
    search_div.appendChild(dropdown_icon);

    // set the wrapper as child (instead of the element)
    element.parentNode.replaceChild(wrapper, element);
    // set element as child of wrapper
    wrapper.appendChild(element);
    wrapper.appendChild(search_div);

    createInitialTokens(element);
    addPlaceholder(wrapper);
}

function removePlaceholder(wrapper) {
    const input_search = wrapper.querySelector(".selected-input");
    input_search.removeAttribute("placeholder");
}

function addPlaceholder(wrapper) {
    const input_search = wrapper.querySelector(".selected-input");
    const tokens = wrapper.querySelectorAll(".selected-wrapper");
    if (!tokens.length && !(document.activeElement === input_search))
        input_search.setAttribute("placeholder", "---------");
}


// Function that create the initial set of tokens with the options selected by the users
function createInitialTokens(select) {
    let {
        options_selected
    } = getOptions(select);
    const wrapper = select.parentNode;
    for (let i = 0; i < options_selected.length; i++) {
        const input_search = wrapper.querySelector(".selected-input");
        const option = wrapper.querySelector(`select option[value="${options_selected[i]}"]`);
        let optionId = option.getAttribute("id");
        let value = options_selected[i];
        if (optionId.includes(',exclude')) {
             value = '<span><span class="uk-icon ourchive-search-badge-exclude" uk-icon="icon: ban; ratio: 1"></span> '
                + " " + value + "</span>";
        }
        createToken(wrapper, value, options_selected[i], optionId+"_dropdown");
        if (document.getElementById(optionId.replace(',mobile', '')+"_badge") !== null) {
            continue;
        }
        createToken(document.getElementById("selected-filters-list"), value, options_selected[i], optionId.replace(',mobile', '')+"_badge");
    }
}


// Listener of user search
function inputChange(e) {
    const wrapper = e.target.parentNode.parentNode;
    const select = wrapper.querySelector("select");
    const dropdown = wrapper.querySelector(".dropdown-icon");

    const input_val = e.target.value;
    if (input_val) {
        dropdown.classList.add("active");
        populateAutocompleteList(select, input_val.trim());
    } else {
        dropdown.classList.remove("active");
        const event = new Event('click');
        dropdown.dispatchEvent(event);
    }
}


// Listen for clicks on the wrapper, if click happens focus on the input
function clickOnWrapper(e) {
    const wrapper = e.target;
    if (wrapper.tagName == "DIV") {
        const input_search = wrapper.querySelector(".selected-input");
        const dropdown = wrapper.querySelector(".dropdown-icon");
        if (!dropdown.classList.contains("active")) {
            const event = new Event('click');
            dropdown.dispatchEvent(event);
        }
        input_search.focus();
        removePlaceholder(wrapper);
    }

}

function openOptions(e) {
    const input_search = e.target;
    const wrapper = input_search.parentElement.parentElement;
    const dropdown = wrapper.querySelector(".dropdown-icon");
    if (!dropdown.classList.contains("active")) {
        const event = new Event('click');
        dropdown.dispatchEvent(event);
    }
    e.stopPropagation();

}

// Function that create a token inside of a wrapper with the given value
function createToken(wrapper, value, text_value, id="") {
    const search = wrapper.querySelector(".search-container");
    // Create token wrapper
    const token = document.createElement("div");
    token.classList.add("selected-wrapper");
    token.setAttribute("id", id);
    const token_span = document.createElement("span");
    token_span.classList.add("selected-label");
    token_span.innerHTML = value;
    const close = document.createElement("a");
    close.classList.add("selected-close");
    close.classList.add("uk-icon");
    close.classList.add("ourchive-search-badge-exclude");
    close.setAttribute("tabindex", "-1");
    close.setAttribute("data-option", text_value);
    close.setAttribute("data-hits", 0);
    close.setAttribute("href", "#");
    close.setAttribute("uk-icon", "icon: ourchive-close; ratio: .8");
    close.addEventListener("click", removeToken);
    token.appendChild(token_span);
    token.appendChild(close);
    wrapper.insertBefore(token, search);
}

// Checkboxes e.g. work type
function handleFacetCheckUncheck(event) {
    checkbox_id = event.target.getAttribute("id").replace(',mobile', '');
    if (event.target.checked) {
        createToken(document.getElementById("selected-filters-list"), event.target.parentNode.innerText, event.target.parentNode.innerText, checkbox_id+"_badge");
    }
    else {
        document.getElementById(checkbox_id+"_badge").remove();
    }
}

// Input e.g. word count
function handleFacetInput(event) {
    let labelParts = event.target.id.split(',');
    let label = labelParts[1] + ": " + event.target.value; 
    if ((event.target.value) && (event.target.value.trim() != '')) {
        input_id = `${event.target.getAttribute("id").replace(',mobile', '')}_badge`;
        if (document.getElementById(input_id) !== null) {
            document.getElementById(input_id).remove();
        }
        createToken(document.getElementById("selected-filters-list"), label, label, input_id);
    }
}


// Listen for clicks in the dropdown option
function clickDropdown(e) {
    const dropdown = e.target;
    const wrapper = dropdown.parentNode.parentNode;
    const input_search = wrapper.querySelector(".selected-input");
    const select = wrapper.querySelector("select");
    dropdown.classList.toggle("active");

    if (dropdown.classList.contains("active")) {
        removePlaceholder(wrapper);
        input_search.focus();

        if (!input_search.value) {
            populateAutocompleteList(select, "", true);
        } else {
            populateAutocompleteList(select, input_search.value);

        }
    } else {
        clearAutocompleteList(select);
        addPlaceholder(wrapper);
    }
}


// Clears the results of the autocomplete list
function clearAutocompleteList(select) {
    const wrapper = select.parentNode;

    const autocomplete_list = wrapper.querySelector(".autocomplete-list");
    autocomplete_list.innerHTML = "";
}

// Populate the autocomplete list following a given query from the user
function populateAutocompleteList(select, query, dropdown = false) {
    const {
        autocomplete_options,
        all_options
    } = getOptions(select);

    let options_to_show;

    if (dropdown)
        options_to_show = autocomplete_options;
    else
        options_to_show = autocomplete(query, autocomplete_options);
    const wrapper = select.parentNode;
    const input_search = wrapper.querySelector(".search-container");
    const autocomplete_list = wrapper.querySelector(".autocomplete-list");
    autocomplete_list.innerHTML = "";
    const result_size = options_to_show.length;

    if (result_size == 1) {

        const li = document.createElement("li");
        li.innerText = options_to_show[0];
        li.setAttribute('data-value', options_to_show[0]);
        li.setAttribute('id', all_options[0].id);
        li.addEventListener("click", selectOption);
        autocomplete_list.appendChild(li);
        if (query.length == options_to_show[0].length) {
            const event = new Event('click');
            li.dispatchEvent(event);

        }
    } else if (result_size > 1) {

        for (let i = 0; i < result_size; i++) {
            const li = document.createElement("li");
            li.innerText = options_to_show[i];
            li.setAttribute('data-value', options_to_show[i]);
            li.setAttribute('id', all_options[i].id);
            li.addEventListener("click", selectOption);
            autocomplete_list.appendChild(li);
        }
    } else {
        const li = document.createElement("li");
        li.classList.add("not-cursor");
        li.innerText = "No options found";
        autocomplete_list.appendChild(li);
    }
}


// Listener to autocomplete results when clicked set the selected property in the select option 
function selectOption(e) {
    const wrapper = e.target.parentNode.parentNode.parentNode;
    const input_search = wrapper.querySelector(".selected-input");
    const option = wrapper.querySelector(`select option[value="${e.target.dataset.value}"]`);

    option.setAttribute("selected", "");
    let optionId = option.getAttribute("id");
    let value = e.target.dataset.value;
    if (optionId.includes(',exclude')) {
         value = '<span><span class="uk-icon ourchive-search-badge-exclude" uk-icon="icon: ban; ratio: 1"></span>' + value + "</span>";
    }
    createToken(wrapper, value, e.target.dataset.value, optionId+"_dropdown");
    createToken(document.getElementById("selected-filters-list"), value, e.target.dataset.value, optionId.replace(',mobile', '')+"_badge");
    if (input_search.value) {
        input_search.value = "";
    }

    input_search.focus();

    e.target.remove();
    const autocomplete_list = wrapper.querySelector(".autocomplete-list");


    if (!autocomplete_list.children.length) {
        const li = document.createElement("li");
        li.classList.add("not-cursor");
        li.innerText = "No options found";
        autocomplete_list.appendChild(li);
    }

    const event = new Event('keyup');
    input_search.dispatchEvent(event);
    e.stopPropagation();
}


// function that returns a list with the autcomplete list of matches
function autocomplete(query, options) {
    // No query passed, just return entire list
    if (!query) {
        return options;
    }
    let options_return = [];

    for (let i = 0; i < options.length; i++) {
        if (query.toLowerCase() === options[i].trim().slice(0, query.length).toLowerCase()) {
            options_return.push(options[i]);
        }
    }
    return options_return;
}


// Returns the options that are selected by the user and the ones that are not
function getOptions(select) {
    // Select all the options available
    const all_options = Array.from(
        select.querySelectorAll("option")
    ).map(function(el) {
        const newOption = Object.assign({}, el);
        newOption.value = el.value;
        newOption.id = el.id;
        return newOption;
    });

    // Get the options that are selected from the user
    const options_selected = Array.from(
        select.querySelectorAll("option:checked")
    ).map(el => el.value);

    // Create an autocomplete options array with the options that are not selected by the user
    const autocomplete_options = [];
    const autocomplete_options_ids = [];
    all_options.forEach(option => {
        if (!options_selected.includes(option.value)) {
            autocomplete_options.push(option.value);
        }
    });

    autocomplete_options.sort();

    return {
        options_selected,
        autocomplete_options,
        all_options
    };

}

// Listener for when the user wants to remove a given token.
function removeToken(e) {
    // Get the value to remove
    const value_to_remove = e.target.closest("a").getAttribute("data-option");
    var ancestor = e.target.closest(".selected-wrapper");
    let token_id = ancestor.getAttribute('id');
    if (token_id == null) {
        token_id = e.target.parentNode.getAttribute('id');
        if (token_id == null) {
            token_id = e.target.parentNode.parentNode.parentNode;   
        }
    }
    let wrapper = null;
    let otherId = null;
    let other_wrapper = null;
    if (token_id.endsWith('_dropdown')) {
        wrapper = e.target.closest(".selected-wrapper").parentNode;
        otherId = token_id.replace(',mobile', '').replace('_dropdown', '_badge');
    }
    else {
        otherId = token_id.replace('_badge', '_dropdown');
        if (document.getElementById(otherId) !== null) {
            wrapper = document.getElementById(otherId).closest(".multi-select-component");
        }
        else {
            otherId = otherId = token_id.replace('_badge', ',mobile_dropdown')
            if (document.getElementById(otherId) !== null) {
                wrapper = document.getElementById(otherId).closest(".multi-select-component");
                console.log(wrapper);
            }
            else {
                var desktop_id = token_id.replace('_badge', '');
                var mobile_id = (token_id.replace('_badge', '')) +',mobile';
                if (document.getElementById(desktop_id).checked || document.getElementById(mobile_id).checked) {
                    document.getElementById(desktop_id).checked = false;
                    document.getElementById(mobile_id).checked = false;
                }
                else {
                    document.getElementById(desktop_id).value = null;
                    document.getElementById(mobile_id).value = null;
                }
            }
        }
    }
    console.log(wrapper);
    if (wrapper !== null) {
        const input_search = wrapper.querySelector(".selected-input");
        const dropdown = wrapper.querySelector(".dropdown-icon");
        // Get the options in the select to be unselected
        const option_to_unselect = wrapper.querySelector(`select option[value="${value_to_remove}"]`);
        option_to_unselect.removeAttribute("selected");
        dropdown.classList.remove("active");
        document.getElementById(otherId).remove();
    }
    // Remove token attribute
    ancestor.remove();
    e.stopPropagation();
}

// Listen for 2 sequence of hits on the delete key, if this happens delete the last token if exist
function deletePressed(e) {
    const wrapper = e.target.parentNode.parentNode;
    const input_search = e.target;
    const key = e.keyCode || e.charCode;
    const tokens = wrapper.querySelectorAll(".selected-wrapper");

    if (tokens.length) {
        const last_token_x = tokens[tokens.length - 1].querySelector("a");
        let hits = +last_token_x.dataset.hits;

        if (key == 8 || key == 46) {
            if (!input_search.value) {

                if (hits > 1) {
                    // Trigger delete event
                    const event = new Event('click');
                    last_token_x.dispatchEvent(event);
                } else {
                    last_token_x.dataset.hits = 2;
                }
            }
        } else {
            last_token_x.dataset.hits = 0;
        }
    }
    return true;
}

// You can call this function if you want to add new options to the select plugin
// Target needs to be a unique identifier from the select you want to append new option for example #multi-select-plugin
// Example of usage addOption("#multi-select-plugin", "tesla", "Tesla")
function addOption(target, val, text) {
    const select = document.querySelector(target);
    let opt = document.createElement('option');
    opt.value = val;
    opt.innerHTML = text;
    select.appendChild(opt);
}

document.addEventListener("DOMContentLoaded", () => {

    // get select that has the options available
    const select = document.querySelectorAll("[data-multi-select-plugin]");
    select.forEach(select => {
        init(select);
    });

    // Dismiss on outside click
    document.addEventListener('click', () => {
        // get select that has the options available
        const select = document.querySelectorAll("[data-multi-select-plugin]");
        for (let i = 0; i < select.length; i++) {
            if (event) {
                var isClickInside = select[i].parentElement.contains(event.target);
                if (!isClickInside) {
                    const wrapper = select[i].parentElement;
                    const dropdown = wrapper.querySelector(".dropdown-icon");
                    const autocomplete_list = wrapper.querySelector(".autocomplete-list");
                    //the click was outside the specifiedElement, do something
                    dropdown.classList.remove("active");
                    autocomplete_list.innerHTML = "";
                    addPlaceholder(wrapper);
                }
            }
        }
    });

});

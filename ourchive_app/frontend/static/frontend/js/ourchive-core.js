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
    console.log(groupName);
    console.log(open);
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
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
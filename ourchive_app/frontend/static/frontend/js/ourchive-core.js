function removeFile(object) {
	document.getElementById(object+'-file-input').value = "";
	document.getElementById(object+'-file-uk-input').value = "";
	console.log(document.getElementById(object+'-file-uk-input-original'));
	document.getElementById(object+'-file-uk-input-original').value = "";
}
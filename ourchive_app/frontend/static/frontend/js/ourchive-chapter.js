function getChapterRichTextValues() {
	if (tinymce.get("summaryEditor") !== null) {
		document.getElementById('summary').value = tinymce.get("summaryEditor").getContent().replace(/\r?\n?/g, '');
	}
	if (tinymce.get("notesEditor") !== null) {
		document.getElementById('notes').value = tinymce.get("notesEditor").getContent().replace(/\r?\n?/g, '');
	}
	document.getElementById('end_notes').value = tinymce.get("end_notesEditor").getContent().replace(/\r?\n?/g, '');
	if (document.getElementById('chapter-text-edit-mode-toggle').checked) {
        document.getElementById('text').value = tinymce.get("textEditor").getContent().replace(/\r?\n?/g, '');
    } else {
        document.getElementById('text').value = document.getElementById('toggle-chapter-plaintext-area').value;
    }
}

function removeChapterImage() {
	console.log(document.getElementById('image_url-file-uk-input-original'));
	document.getElementById('image_url-file-uk-input-original').value = "";
	document.getElementById('chapter-form-image').src = "";
}

function updateModeText(toggling=false) {
	const richTextContainer = document.getElementById('toggle-chapter-richtext-area');
	const plainTextContainer = document.getElementById('toggle-chapter-plaintext-area');
	if (document.getElementById('chapter-text-edit-mode-toggle').checked) {
		tinymce.get("textEditor").setContent(document.getElementById('toggle-chapter-plaintext-area').value);
		localStorage.setItem('rich-text', true);
		plainTextContainer.setAttribute('hidden', true);
		richTextContainer.removeAttribute('hidden');
	}
	else {
		if (toggling) {
			const grafEx = new RegExp('<p>', "g");
			const whEx = new RegExp('</p>', "g");
			document.getElementById('toggle-chapter-plaintext-area').innerHTML = tinymce.get("textEditor").getContent().replace(/\r?\n?/g, '').replace(grafEx, '\n').replace(whEx, '').replace('\n', '');
		}
		localStorage.setItem('rich-text', false);
		richTextContainer.setAttribute('hidden', true);
		plainTextContainer.removeAttribute('hidden');
	}
}

function chapterTextInit() {
	// This handles user preferences in local storage for whether they prefer rich text or plain text/HTML input.
	let richTextPreference = localStorage.getItem('rich-text');
	const richTextCheckbox = document.querySelector('#chapter-text-edit-mode-toggle');
	// This data is saved in local storage as a string, and we want to default to rich text mode.
	richTextCheckbox.checked = richTextPreference !== 'false';
	updateModeText();
}
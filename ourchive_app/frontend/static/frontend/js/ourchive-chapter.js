function getChapterRichTextValues() {
	document.getElementById('summary').value = tinymce.get("summaryEditor").getContent().replace(/\r?\n?/g, '');
	document.getElementById('notes').value = tinymce.get("notesEditor").getContent().replace(/\r?\n?/g, '');
	document.getElementById('end_notes').value = tinymce.get("end_notesEditor").getContent().replace(/\r?\n?/g, '');
	if (document.getElementById('chapter-text-edit-mode-toggle').checked) {
        document.getElementById('chapter_text').value = tinymce.get("chapterTextEditor").getContent().replace(/\r?\n?/g, '');
    } else {
        document.getElementById('chapter_text').value = document.getElementById('toggle-chapter-plaintext-area').value;
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
		tinymce.get("chapterTextEditor").setContent(document.getElementById('toggle-chapter-plaintext-area').value);
		localStorage.setItem('rich-text', true);
		plainTextContainer.setAttribute('hidden', true);
		richTextContainer.removeAttribute('hidden');
	}
	else {
		if (toggling) {
			const grafEx = new RegExp('<p>', "g");
			const whEx = new RegExp('</p>', "g");
			document.getElementById('toggle-chapter-plaintext-area').innerHTML = tinymce.get("chapterTextEditor").getContent().replace(/\r?\n?/g, '').replace(grafEx, '\n').replace(whEx, '').replace('\n', '');
		}
		localStorage.setItem('rich-text', false);
		richTextContainer.setAttribute('hidden', true);
		plainTextContainer.removeAttribute('hidden');
	}
}

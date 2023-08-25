function getChapterRichTextValues() {
	document.getElementById('chapter_summary').value = tinymce.get("chapterSummaryEditor").getContent().replace(/\r?\n?/g, '');
	document.getElementById('chapter_notes').value = tinymce.get("chapterNotesEditor").getContent().replace(/\r?\n?/g, '');
	document.getElementById('chapter_end_notes').value = tinymce.get("chapterEndNotesEditor").getContent().replace(/\r?\n?/g, '');
	if (document.getElementById('chapter-text-edit-mode-toggle').checked) {
        document.getElementById('chapter_text').value = tinymce.get("chapterTextEditor").getContent().replace(/\r?\n?/g, '');
    } else {
        document.getElementById('chapter_text').value = document.getElementById('toggle-chapter-plaintext-area').value;
    }
}

function updateModeText() {
	if (document.getElementById('chapter-text-edit-mode-toggle').checked) {
		tinymce.get("chapterTextEditor").setContent(document.getElementById('toggle-chapter-plaintext-area').value);
	}
	else {
		const grafEx = new RegExp('<p>', "g");
		const whEx = new RegExp('</p>', "g");
		document.getElementById('toggle-chapter-plaintext-area').innerHTML = tinymce.get("chapterTextEditor").getContent().replace(/\r?\n?/g, '').replace(grafEx, '\n').replace(whEx, '').replace('\n', '');
	}
}
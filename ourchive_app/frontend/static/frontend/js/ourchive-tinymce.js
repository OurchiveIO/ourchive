function getRichText(formFields) {
    formFields.forEach((formFieldId) => {
        document.getElementById(formFieldId).value = tinymce.get(formFieldId+'Editor').getContent().replace(/\r?\n?/g, '');
    });
}
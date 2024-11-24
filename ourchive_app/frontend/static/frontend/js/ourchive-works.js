window.addEventListener("load", function() {
        initShowMores('work', 'works-tag-container', 'works-summary-container', 'tags', 'summary');
    });

function addSelectedCollection() {
    document.querySelectorAll('.add-to-bookmark-radio').forEach(function(elm)
    {
        if (elm.checked === true) {
            var url = "{% url 'fe-add-collection-to-bookmark' work.id %}";
            window.open(url + '?collection_id=' + elm.name, '_blank');
        }
    });
}

function updateChapter(currentId, currentNumber, workId) {
    var selectedOption = document.getElementById("work-chapter-select").value.split(',');
    var href = "";
    if (selectedOption[0] === "-1") {
        href = `/works/${workId}/`
    }
    else if (selectedOption[0] === "-2") {
        href = `/works/${workId}/?view_full=true`
    }
    else {
        let offset = selectedOption[1] - 1;
        href = `/works/${workId}/${offset}`;
    }
    window.location.href = href;
}
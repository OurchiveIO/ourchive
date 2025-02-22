function loadMoreComments(next, chapterId, bookmark_id) {
    fetch(next)
      .then((response) => {
        return response.text();
      })
      .then((myText) => {
        document.getElementById(`bookmark-${bookmark_id}-comments-child-container`).innerHTML = "";
        document.getElementById(`bookmark-${bookmark_id}-comments-child-container`).innerHTML = myText;
        document.getElementById(`bookmark-${bookmark_id}-comments-child-container`).scrollIntoView();
      });
}

function colorStar(starNum) {
    if (!document.getElementById("rating_"+starNum).classList.contains("rating-star")) {
        for (let star = 1; star <= starNum; star++) {
            document.getElementById("rating_"+star).classList.add("rating-star");
            document.getElementById(`rating_${star}_icon`).classList.remove("bi-star");
            document.getElementById(`rating_${star}_icon`).classList.add("bi-star-fill");
            document.getElementById("bookmark_rating").setAttribute("value", star);
        }
    }
    else {
        for (let star = starNum + 1; star <= 100; star++) {
            var element = document.getElementById("rating_"+star);
            if (element == null) break;
            document.getElementById("rating_"+star).classList.remove("rating-star");
            document.getElementById(`rating_${star}_icon`).classList.remove("bi-star-fill");
            document.getElementById(`rating_${star}_icon`).classList.add("bi-star");
        }
        document.getElementById("bookmark_rating").setAttribute("value", starNum);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initializeMultiSelect('bookmark-form-languages');
    initializeEditTags();
});
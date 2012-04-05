
/* links all hashtags in all comments in the page */
format_hashtags = function(newtab) {   
    $('.comment-text').each(function(i, l) {
        l.innerHTML =  link_hashtags(l.textContent, newtab);
    });
}

/* Returns the text given with all instances of "#hashtag" linked to its wiki page */
link_hashtags = function(html, newtab) {
    output = html;
    for (k in hashtags) {
        var r = new RegExp('(\#' + k + ')', 'gi');
        if (k == 'important') {
            output = output.replace(r, "<a class='hashtag-important' onclick=hashtag_redirect(hashtags[k]," + newtab + ")>$1</a>");
        } else {
            output = output.replace(r, "<a style='cursor:pointer' onclick=hashtag_redirect(hashtags[k]," + newtab + ")>$1</a>");
        }
    }
    
    return output;
}


function hashtag_redirect(text, newtab) {
    if (newtab) {
        window.open(text);
    } else {
        window.location = text;
    }
}
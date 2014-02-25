
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
            output = output.replace(r, "<a class='hashtag-important' onclick=hashtag_redirect('" + hashtags[k]+ "'," + newtab + ")>$1</a>");
        } else {
            output = output.replace(r, "<a style='cursor:pointer' onclick=hashtag_redirect('" + hashtags[k] + "'," + newtab + ") contenteditable='false'>$1</a>");
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



// overrides onclick functionality of scrolling comments
function hashtagRedirect(text) {
    window.open(text, '_newtab');
}

function getFormattedHashtagText(text) {
    var output = text.replace(/(#important[^\w])/ig, '<span class="hashtag-important">$1</span>');
    output = output.replace(/(#magicnumber[^\w])/ig, '<a onclick=hashtagRedirect("http://c2.com/cgi/wiki?MagicNumber")>$1</a>');
    output = output.replace(/(#namingconvention[^\w])/ig, '<a onclick=hashtagRedirect("http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-135099.html#367")>$1</a>');
    output = output.replace(/(#javadoc[^\w])/ig, '<a onclick=hashtagRedirect("http://www.oracle.com/technetwork/java/javase/documentation/index-137868.html")>$1</a>');
    output = output.replace(/(#import[^\w])/ig, '<a onclick=hashtagRedirect("http://checkstyle.sourceforge.net/config_imports.html")>$1</a>');
    output = output.replace(/(#braces[^\w])/ig, '<a onclick=hashtagRedirect("http://www.oracle.com/technetwork/java/javase/documentation/codeconventions-142311.html#430")>$1</a>');
    output = output.replace(/(#modifierorder[^\w])/ig, '<a onclick=hashtagRedirect("http://checkstyle.sourceforge.net/config_modifier.html")>$1</a>');
    output = output.replace(/(#size[^\w])/ig, '<a onclick=hashtagRedirect("http://checkstyle.sourceforge.net/config_sizes.html")>$1</a>');
    output = output.replace(/(#innerassignment[^\w])/ig, '<a onclick=hashtagRedirect("http://checkstyle.sourceforge.net/config_coding.html#InnerAssignment")>$1</a>');
    output = output.replace(/(#hashcode[^\w])/ig, '<a onclick=hashtagRedirect("http://www.technofundo.com/tech/java/equalhash.html")>$1</a>');
    output = output.replace(/(#scope[^\w])/ig, '<a onclick=hashtagRedirect("http://geosoft.no/development/javastyle.html#Variables")>$1</a>');
    output = output.replace(/(#defaultclause[^\w])/ig, '<a onclick=hashtagRedirect("http://stackoverflow.com/questions/4649423/should-switch-statements-always-contain-a-default-clause")>$1</a>');
    output = output.replace(/(#emptystatement[^\w])/ig, '<a onclick=hashtagRedirect("http://stackoverflow.com/questions/14112515/semicolon-at-end-of-if-statement")>$1</a>');
    output = output.replace(/(#modifierorder[^\w])/ig, '<a onclick=hashtagRedirect("http://stackoverflow.com/questions/16731240/what-is-a-reasonable-order-of-java-modifiers-abstract-final-public-static-e")>$1</a>');
    output = output.replace(/(#tab[^\w])/ig, '<a onclick=hashtagRedirect("http://www.jwz.org/doc/tabs-vs-spaces.html")>$1</a>');

    return output;
}

function formatHashtags() {
    $('.comment-text').each(function(i, l) {
        $(l).html(getFormattedHashtagText($(l).html()));
    });
}
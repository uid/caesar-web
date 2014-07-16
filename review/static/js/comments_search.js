// Store a cookie of the user's preference for hiding or showing similar comment suggestions
var showSimilarCommentsState = $.cookie('showSimilarCommentsState') || 'expanded';

function createSimilarCommentsDiv(comment_type) {
  var comment_header = $("<div class='comment-header'></span>");
  var comment_header_text = $("<span class='comment-header-text'>0 matching comments</span>")
  var comment_visibility = $("<span class='comment-visibility'></span>");
  comment_header.append(comment_visibility, comment_header_text);
  var similar_comments_wrapper = $("<div class='similar-comments-wrapper'></div>");
  var similar_comments_display = $("<div class='similar-comments-display "+showSimilarCommentsState+" "+comment_type+"'>");
  similar_comments_display.append(comment_header, similar_comments_wrapper);
  $(".new-"+comment_type).after(similar_comments_display);

  // Add listener to header, so user can collapse comment display
  $(comment_header).on("click", function() {
    if ($(similar_comments_display).hasClass("expanded")) { // Collapse similar comments
      $.cookie('showSimilarCommentsState', 'collapsed');
      $(similar_comments_wrapper).hide(effect="blind", complete=function() {
        $(similar_comments_display).removeClass("expanded");
        $(similar_comments_display).addClass("collapsed");
      });
    }
    else { // Expand similar comments
      $.cookie('showSimilarCommentsState', 'expanded');
      $(similar_comments_display).addClass("expanded");
      $(similar_comments_display).removeClass("collapsed");
      $(similar_comments_wrapper).show(effect="blind");
    }
  });
}

// Remove all similar-comment divs whenever the user closes a new comment entry box.
function removeSimilarCommentsDiv(comment_type) {
  $(".similar-comments-display").remove();
}

// Clear similarCommentsDB database !important
function clearDatabase(chunk_id) {
  var db;
  if ($.browser.mozilla) {
    /*var request = indexedDB.open('similarCommentsDB-'+chunk_id);
    request.onerror = function(event) {
      alert("Why didn't you allow my web app to use IndexedDB?!");
    };
    request.onsuccess = function(event) {
      db = request.result;
      function clearStore(store_name) {
        var tx = db.transaction(store_name, 'readwrite');
        var store = tx.objectStore(store_name);
        store.clear();
      }
      clearStore('fullproofmetadata');
      clearStore('normalindex');
      clearStore('stemmedindex');
    };*/
  }
  else {
    db = openDatabase('similarCommentsDB-'+chunk_id, '1.0', 'similarCommentsDB-'+chunk_id, 2 * 1024 * 1024);
    db.transaction(function (tx) {
      tx.executeSql('DROP TABLE fullproofmetadata');
      tx.executeSql('DROP TABLE normalindex');
      tx.executeSql('DROP TABLE stemmedindex');
    });
  }
}

var commentSearch = new function() {

  var dbName, commentsSearchEngine, commentsData, commentsExtraData;

  var initializer = function(injector, callback) {
    var commentsData_copy = commentsData.slice(0);
    var synchro = fullproof.make_synchro_point(callback, commentsData_copy.length-1);
    var values = [];
    for (var i=0;i<commentsData_copy.length; ++i) {
      values.push(i);
    }
    injector.injectBulk(commentsData, values, callback);      
  }

  var engineReady = function(b) {
    if (!b) {
      alert("Can't load the search engine!");
    }
  }

  this.init = function(commentsData_, commentsExtraData_, chunk_id) {

    dbName = "similarCommentsDB-"+chunk_id;
    commentsSearchEngine = new fullproof.ScoringEngine();
    commentsData = commentsData_;
    commentsExtraData = commentsExtraData_;
    var index1 = new fullproof.IndexUnit(
      "normalindex",
      new fullproof.Capabilities().setStoreObjects(false).setUseScores(true).setDbName(dbName).setComparatorObject(fullproof.ScoredEntry.comparatorObject).setDbSize(8*1024*1024),
      new fullproof.ScoringAnalyzer(fullproof.normalizer.to_lowercase_nomark, fullproof.english.stopword_remover, fullproof.normalizer.remove_duplicate_letters),
      initializer
    );

    var index2 = new fullproof.IndexUnit(
      "stemmedindex",
      new fullproof.Capabilities().setStoreObjects(false).setUseScores(true).setDbName(dbName).setComparatorObject(fullproof.ScoredEntry.comparatorObject).setDbSize(8*1024*1024),
      new fullproof.ScoringAnalyzer(fullproof.normalizer.to_lowercase_nomark, fullproof.english.metaphone),
      initializer
    );

    commentsSearchEngine.open([index1,index2], fullproof.make_callback(engineReady, true), fullproof.make_callback(engineReady, false));

  };

  this.search = function(value, similarCommentClass) {

    // Create regular expression for highlighting query words]
    var wordset = value.replace(/\n|\r/g, " ").split(" ");
    var patternset = [];
    for (var i in wordset) {
      // stopwords is a list of stopwords from stopwords.js. This is a copy of the stopwords used by fullproof.
      if (stopwords.indexOf(wordset[i]) == -1) {
        patternset.push(wordset[i]);
      }
    }
    var pattern = patternset.join("|");
    var regex = new RegExp(pattern, "ig");

    // Request a search to the comments engine, then displays the results, if any.
    try {
      commentsSearchEngine.lookup(value, function(resultset) {
        var results = [];
        if (resultset && resultset.getSize()) {
          // resultset is a fullproof object that has its own forEach method
          resultset.forEach(function(e) {
            if (e.score >= 2.5) {
              results.push({
                "index": e.value,
                "score": e.score,
                "bag_of_words": regex.exec(commentsData[e.value]),
              });              
            }
          });
        }

        // Sort results from highest score to lowest score
        results.sort(function(a,b) { return b.score - a.score; });

        var ids = [];

        // Display only the top 3 results.
        // Use .html() rather than .text() to deal with special characters.
        for (var i=0; i<Math.min(results.length, 3); i++) {

          ids.push('#'+similarCommentClass+'-'+results[i].index);

           // Check whether this result is already displayed
          if ($('#'+similarCommentClass+'-'+results[i].index).length != 0) {
            var comment_div = $('#'+similarCommentClass+'-'+results[i].index);
            var text = $(comment_div).find(".comment-form .similar-comment-text").html();
            $(comment_div).find(".comment-form .similar-comment-text").html(text.replace(regex, '<i><b>$&</b></i>'));
            var matches = commentsData[results[i].index].match(regex);
            $(comment_div).find(".comment-header .comment-title").text(matches.join());

            if (comment_div.index() != i) {
              $('.similar-comments-wrapper > div:nth-child('+i+')').after(comment_div);
              $(comment_div).hide();
              $(comment_div).show("blind");
            }
            continue;
          }

          var comment_div = $("<div class='comment collapsed'></div>");
          comment_div.addClass(similarCommentClass);
          comment_div.attr("id", similarCommentClass+"-"+results[i].index);

          // Link to comment in context
          var comment_header = $("<div class='comment-header'></div>");
          var matches = commentsData[results[i].index].match(regex);
          var title = $("<div class='comment-title'></div>");
          title.text(matches.join());
          comment_header.append(title);

          // Print the comment in a div
          var comment_form = $("<div class='comment-form'></div>");
          var comment_textdiv = $("<div></div>");
          comment_textdiv.addClass(similarCommentClass+"-text");
          comment_textdiv.html(commentsData[results[i].index].replace(regex, '<i><b>$&</b></i>'));
          comment_form.append(comment_textdiv);

          // Who wrote this comment and when?
          var comment_author = $("<div class='comment-author'></div>");
          var clipboard_button = $("<button class='clippy-button ui-button ui-widget ui-state-default ui-corner-all ui-button-icon-only' type='button' role='button' aria-disabled='false' title='Copy to clipboard'><span class='ui-button-icon-primary ui-icon ui-icon-clippy'></span><span class='ui-button-text'>Copy to clipboard</span></button>");
          clipboard_button.attr("id", "clipboard-button-"+results[i].index);
          clipboard_button.attr("data-clipboard-text", commentsData[results[i].index]);
          // Set up ZeroClipboard which copies the text in comment_textdiv to the clipboard when user clicks on clipboard_button.
          var client = new ZeroClipboard(clipboard_button);
          client.on("ready", function() {
            this.on("aftercopy", function(event) {
              $(event.target).attr("title", "Copied!");
            });
          });
          comment_author.append(clipboard_button);

          comment_author.append(commentsExtraData[results[i].index].date+" ago");
          if (commentsExtraData[results[i].index].author != "") {
            var author_link = $("<a target='_blank'></a>");
            author_link.attr("href", commentsExtraData[results[i].index].author_url);
            author_link.html(commentsExtraData[results[i].index].author);
            comment_author.append(" by ", author_link);
          }

          // Link to comment in context
          var comment_footer = $("<div class='comment-footer'></div>");
          var see_context_button = $("<button class='comment-chunk-button ui-button ui-widget ui-state-default ui-corner-all ui-button-icon-only' type='button' role='button' aria-disabled='false' title='See context'><span class='ui-button-icon-primary ui-icon ui-icon-robot'></span><span class='ui-button-text'>See context</span></button>");
          see_context_button.attr("onclick", "window.open('"+commentsExtraData[results[i].index].chunk_url+"')");
          comment_footer.append(see_context_button);

          comment_div.append(comment_header, comment_author, comment_form, comment_footer);

          // Add new similar comment to after the previous result, in the correct order
          if (i == 0) { // This is the first result to be displayed
            $('.similar-comments-wrapper').prepend(comment_div);
          }
          else {
            // jQuery is stupid and 1-indexes its selectors, thus using i rather i-1
            $('.similar-comments-wrapper > div:nth-child('+i+')').after(comment_div);
          }
          $(comment_div).hide();
          $(comment_div).show("blind");

          $(comment_div).data("wasClicked", false);

          // Listeners to appropriately expand and collapse comments when you hover or click on them
          // When you hover over a comment, it should expand
          // When you click on a comment header, it should stay expanded
          $("#"+similarCommentClass+"-"+results[i].index+" .comment-header").on("click", function() {
            var this_comment = $(this).parent();
            var wasClicked = this_comment.data("wasClicked");
            if (wasClicked && this_comment.hasClass("expanded")) {
              this_comment.removeClass("expanded");
              this_comment.addClass("collapsed");
            }
            else if (!wasClicked) {
              this_comment.addClass("expanded");
              this_comment.removeClass("collapsed");
            }
            this_comment.data("wasClicked", !wasClicked);
          });

          $(comment_div).on("mouseenter", function() {
            var wasClicked = $(this).data("wasClicked");
            if (!wasClicked && $(this).hasClass("collapsed")) {
              $(this).addClass("expanded");
              $(this).removeClass("collapsed");
            }
          });

          $(comment_div).on("mouseleave", function() {
            var wasClicked = $(this).data("wasClicked");
            if (!wasClicked && $(this).hasClass("expanded")) {
              $(this).removeClass("expanded");
              $(this).addClass("collapsed");
            }
          });

        }

        // Remove results that weren't in the top 3
        var selectorString = ".".concat(similarCommentClass)
                                .concat(":not(")
                                .concat(ids.join())
                                .concat(")");
        $(selectorString).remove();

        // Update the number of matching comments, displayed in the header
        $(".comment-header-text").text(ids.length+" matching comments");

      });
    } catch(err) {
      // fullproof engine throws an error when the only query words are stopwords (or the query is empty).
      // This is ok because there will be 0 similar comments, so just hard code this.

      $(".similar-comments-wrapper").empty();
      // Update the number of matching comments, displayed in the header
      $(".comment-header-text").text("0 matching comments");
    }
  };

}
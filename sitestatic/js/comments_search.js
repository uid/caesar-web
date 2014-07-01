function createSimilarCommentsDiv(comment_type) {
  var comment_header = $("<div class='comment-header'></span>");
  var comment_visibility = $("<span class='comment-visibility'></span>");
  comment_header.append("0 matching comments", comment_visibility);
  var similar_comments_wrapper = $("<div id='similar-comments-wrapper'></div>");
  var similar_comments_display = $("<div class='similar-comments-display "+comment_type+"'>");
  similar_comments_display.append(comment_header, similar_comments_wrapper);
  $(".new-"+comment_type).after(similar_comments_display);
}

// Remove all similar-comment divs whenever the user closes a new comment entry box.
function removeSimilarCommentsDiv(comment_type) {
  $(".similar-comments-display").remove();
}

var commentSearch = new function() {

  var dbName = "similarCommentsDB";
  var commentsSearchEngine = new fullproof.ScoringEngine();
  var commentsData = []
  var commentsExtraData = []

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

  this.init = function(commentsData_, commentsExtraData_) {

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

    // Clear similarCommentsDB database !important
    var db = openDatabase('similarCommentsDB', '1.0', 'similarCommentsDB', 2 * 1024 * 1024);
    db.transaction(function (tx) {
      tx.executeSql('DROP TABLE fullproofmetadata');
      tx.executeSql('DROP TABLE normalindex');
      tx.executeSql('DROP TABLE stemmedindex');
    });

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
    commentsSearchEngine.lookup(value, function(resultset) {
      var results = [];
      if (resultset && resultset.getSize()) {
        // resultset is a fullproof object that has its own forEach method
        resultset.forEach(function(e) {
          // Only choose scores that are "good enough"
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
          if (comment_div.index() != i) {
            $('#similar-comments-wrapper > div:nth-child('+i+')').after(comment_div);
            var text = $(comment_div).find(".comment-form .similar-comment-text").html();
            $(comment_div).find(".comment-form .similar-comment-text").html(text.replace(regex, '<i><b>$&</b></i>'));
            $(comment_div).hide();
            $(comment_div).show("blind");
          }
          continue;
        }

        var comment_div = $("<div class='comment "+similarCommentClass+"' id='"+similarCommentClass+"-"+results[i].index+"'></div>");

        // Link to comment in context
        var comment_chunkdiv = $("<div class='comment-header'></div>");
        var comment_chunk_link = $("<a target='_blank'></a>");
        comment_chunk_link.attr("href", commentsExtraData[results[i].index].chunk_url);
        comment_chunk_link.html(commentsExtraData[results[i].index].chunk_name);
        comment_chunkdiv.append(comment_chunk_link);

        // Who wrote this comment and when?
        var comment_author = $("<div class='comment-author'></div>");
        comment_author.html(commentsExtraData[results[i].index].date+" ago");
        if (commentsExtraData[results[i].index].author != "") {
          var author_link = $("<a target='_blank'></a>");
          author_link.attr("href", commentsExtraData[results[i].index].author_url);
          author_link.html(commentsExtraData[results[i].index].author);
          comment_author.append(" by ", author_link);
        }

        // Print the comment in a div
        var comment_form = $("<div class='comment-form'></div>");
        var clipboard_button = $("<button class='clippy-button ui-button ui-widget ui-state-default ui-corner-all ui-button-icon-only' type='button' role='button' aria-disabled='false' title='Copy to clipboard'><span class='ui-button-icon-primary ui-icon ui-icon-clippy'></span><span class='ui-button-text'>Copy to clipboard</span></button>");
        var comment_textdiv = $("<div class='"+similarCommentClass+"-text'></div>").html(commentsData[results[i].index].replace(regex, '<i><b>$&</b></i>'));
        comment_form.append(clipboard_button, comment_textdiv);

        comment_div.append(comment_chunkdiv, comment_author, comment_form);

        // Add new similar comment to after the previous result, in the correct order
        if (i == 0) { // This is the first result to be displayed
          $('#similar-comments-wrapper').prepend(comment_div);
        }
        else {
          // jQuery is stupid and 1-indexes its selectors, thus using i rather i-1
          $('#similar-comments-wrapper > div:nth-child('+i+')').after(comment_div);
        }
        $(comment_div).hide();
        $(comment_div).show("blind");
      }

      // Remove results that weren't in the top 3
      var selectorString = ".".concat(similarCommentClass)
                              .concat(":not(")
                              .concat(ids.join())
                              .concat(")");
      $(selectorString).remove();

    });
  };

}
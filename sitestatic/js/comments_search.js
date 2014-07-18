function createSimilarCommentWrapper(comment_type) {
  var similar_comment_wrapper = $("<div class='similar-"+comment_type+"-wrapper'></div>");
  $(".new-"+comment_type).after(similar_comment_wrapper);
}

// Remove all similar comment/reply wrappers whenever the user closes a new comment entry box.
function removeSimilarCommentWrapper(comment_type) {
  $(".similar-"+comment_type+"-wrapper").remove();
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

  this.search = function(value, comment_type) {

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

          ids.push('#similar-comment-'+results[i].index);

           // Check whether this result is already displayed
          if ($('#similar-comment-'+results[i].index).length != 0) {
            var comment_div = $('#similar-comment-'+results[i].index);
            var text = $(comment_div).find(".similar-comment-text").html();
            $(comment_div).find(".similar-comment-text").html(text.replace(regex, '<i><b>$&</b></i>'));

            if (comment_div.index() != i) {
              $('.similar-'+comment_type+'-wrapper > div:nth-child('+i+')').after(comment_div);
              $(comment_div).hide();
              $(comment_div).show("blind");
            }
            continue;
          }

          var comment_div = $("<div class='comment'></div>");
          comment_div.addClass("similar-comment");
          comment_div.attr("id", "similar-comment-"+results[i].index);

          // Print the comment in a div
          var comment_text = $("<div></div>");
          comment_text.addClass("similar-comment-text");
          comment_text.html(commentsData[results[i].index].replace(regex, '<i><b>$&</b></i>'));

          comment_div.append(comment_text);

          // Add new similar comment to after the previous result, in the correct order
          if (i == 0) { // This is the first result to be displayed
            $('.similar-'+comment_type+'-wrapper').prepend(comment_div);
          }
          else {
            // jQuery is stupid and 1-indexes its selectors, thus using i rather i-1
            $('.similar-'+comment_type+'-wrapper > div:nth-child('+i+')').after(comment_div);
          }
          $(comment_div).hide();
          $(comment_div).show("blind");

        }

        // Remove results that weren't in the top 3
        var selectorString = ".".concat("similar-comment")
                                .concat(":not(")
                                .concat(ids.join())
                                .concat(")");
        $(selectorString).remove();

      });
    } catch(err) {
      // fullproof engine throws an error when the only query words are stopwords (or the query is empty).
      // This is ok because there will be 0 similar comments, so just hard code this.

      $(".similar-"+comment_type+"-wrapper").empty();
    }
  };

}
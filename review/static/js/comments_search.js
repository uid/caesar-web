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
      new fullproof.ScoringAnalyzer(fullproof.normalizer.to_lowercase_nomark, fullproof.normalizer.remove_duplicate_letters),
      initializer
    );

    var index2 = new fullproof.IndexUnit(
      "stemmedindex",
      new fullproof.Capabilities().setStoreObjects(false).setUseScores(true).setDbName(dbName).setComparatorObject(fullproof.ScoredEntry.comparatorObject).setDbSize(8*1024*1024),
      new fullproof.ScoringAnalyzer(fullproof.normalizer.to_lowercase_nomark, fullproof.english.metaphone),
      initializer
    );

    //console.log(fullproof.english.metaphone("Absolutly"));
    //console.log(fullproof.french.stopword_remover("JOHN"));

    commentsSearchEngine.open([index1,index2], fullproof.make_callback(engineReady, true), fullproof.make_callback(engineReady, false));
    // Clear similarCommentsDB database !important
    var db = openDatabase('similarCommentsDB', '1.0', 'similarCommentsDB', 2 * 1024 * 1024);
    db.transaction(function (tx) {
      tx.executeSql('DROP TABLE fullproofmetadata');
      tx.executeSql('DROP TABLE normalindex');
      tx.executeSql('DROP TABLE stemmedindex');
    });

  };

  this.search = function(value, targetClass, similarCommentClass) {
    $("."+similarCommentClass).remove();
    var pattern = value.replace(/\s|\n|\r/g, "|");
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
              "bag_of_words": regex.exec(commentsData[e.value])
            });
          }
        });
      }

      // Sort results from highest score to lowest score
      results.sort(function(a,b) { return b.score - a.score; });

      var similar_comment_wrapper = $("<div class='collapsable-wrapper expanded'></div>");
      var visibility = $("<span class='comment-visibility'></span>");
      similar_comment_wrapper.append(visibility);

      // Display only the top 3 results.
      // Use .html() rather than .text() to deal with special characters.
      for (var i=0; i<Math.min(results.length, 3); i++) {
        var comment_div = $("<div class='comment "+similarCommentClass+" expanded'></div>");

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
        var comment_textdiv = $("<div class='"+similarCommentClass+"-text'></div>").html(commentsData[results[i].index].replace(regex, '<i><b>$&</b></i>'));
        comment_form.append(comment_textdiv);

        comment_div.append(comment_chunkdiv, comment_author, comment_form);
        similar_comment_wrapper.append(comment_div);
          
      }
      $("."+targetClass).after(similar_comment_wrapper);

      // Animate showing similar comments
      $(similar_comment_wrapper).hide();
      $(similar_comment_wrapper).show("blind");
    });
  };

}
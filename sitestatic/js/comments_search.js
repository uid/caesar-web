function setupSimilarComments(comment_type) {

  var ascii_keys = {9: "tab", 13: "return", 37: "left", 38: "up", 39: "right", 40: "down"};

  var halt_search = false;

  // Create similar-comment wrapper
  var similar_comment_wrapper = $("<div class='similar-"+comment_type+"-wrapper'></div>");
  $(".new-"+comment_type).after(similar_comment_wrapper);

  // Remove similar-comment wrapper whenever the user closes a new comment entry box.
  $(".new-"+comment_type).on("remove", function(e) {
    $(".similar-"+comment_type+"-wrapper").remove();
  });

  function removeFeedback(textentry) {
    $("#feedback").remove();
  }

  function addFeedback(textentry, similar_comment) {
    var feedback = $("<div id='feedback'></div>");
    feedback.text(similar_comment);
    textentry.append(feedback);
  }

  function selectNext() {
    var selected = $(".selected");
    if (selected.hasClass("new-"+comment_type)) {
      $(".similar-comment:first").addClass("selected");
      selected.removeClass("selected");
    }
    else if (selected.next().length > 0) {
      selected.next().addClass("selected");
      selected.removeClass("selected");
    }
  }

  function selectPrevious() {
    var selected = $(".selected");
    if (selected.is(".similar-comment:first")) {
      $(".new-"+comment_type).addClass("selected");
      selected.removeClass("selected");
    }
    else if (!selected.hasClass("new-"+comment_type)) {
      $(selected).prev().addClass("selected");
      $(selected).removeClass("selected");
    }
  }

  // Copy textentry text to hidden form textarea, and perform search
  $("#textentry").on("keydown", function(event) {
    if (halt_search) {
      return;
    }
    if (event.which in ascii_keys) {
      var textentry = $(this);
      var user_entry = textentry.clone();
      user_entry.find("#feedback").remove();

      // Get text content from contenteditable div
      var content = $("<pre />").html(user_entry.html());
      if ($.browser.webkit) {
        content.find("div").replaceWith(function() {
          return "\n" + this.innerHTML;
        });
      }
      if ($.browser.msie) {
        content.find("p").replaceWith(function() {
          return this.innerHTML + "<br>";
        });
      }
      if ($.browser.mozilla || $.browser.opera || $.browser.msie) {
        content.find("br").replaceWith("\n");
      }
      content = content.text();

      // Get line number of cursor
      var lines = content.split("\n");
      var line_text = window.getSelection().getRangeAt(0).commonAncestorContainer.textContent;
      var line_num = lines.indexOf(line_text);

      // Check if cursor is on last line
      if (line_num == lines.length - 1) {
        var cursor_position = window.getSelection().getRangeAt(0).startOffset;
        var length = line_text.length;

        // Check if cursor is at last character of the line
        if (cursor_position == length) {
          if (ascii_keys[event.which] == "down" || ascii_keys[event.which] == "right" || ascii_keys[event.which] == "tab") {
            selectNext();
            removeFeedback(textentry);
            addFeedback(textentry, $(".selected .similar-comment-text").text());
            return false;
          }
          else if (ascii_keys[event.which] == "up" || ascii_keys[event.which] == "left") {
            if ($(".selected").length != 0) {
              selectPrevious();
              removeFeedback(textentry);
              if ($(".selected").length != 0) {
                addFeedback(textentry, $(".selected .similar-comment-text").text());
              }
              return false;
            }
          }
          else if (ascii_keys[event.which] == "return") {
            feedback_text = $("#feedback").text();
            $(this).append(feedback_text);
            removeFeedback($(this));
            $(".selected").removeClass("selected");
            $(".similar-"+comment_type+"-wrapper").empty();
            halt_search = true;
          }
        }
      }
    }
  });

  $("#textentry").on("keyup", function(event) {
    if ($(this).html() == "") {
      halt_search = false;
    }
    if (halt_search) {
      return;
    }
    if (!(event.which in ascii_keys)) {
      removeFeedback($(this));
      $(".similar-comment.selected").removeClass("selected");
      var textentry_text = $(this).text();
      $("#hidden-textarea").val(textentry_text);
      commentSearch.search(textentry_text, comment_type);
    }
  });

  $("#textentry").focus();
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
      console.log("Can't load the search engine!");
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

    // Create regular expression for highlighting query words
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
        for (var i=0; i<Math.min(results.length, 3); i++) {

          ids.push('#similar-comment-'+results[i].index);

           // Check whether this result is already displayed
          if ($('#similar-comment-'+results[i].index).length != 0) {
            var comment_div = $('#similar-comment-'+results[i].index);
            var text = $(comment_div).find(".similar-comment-text").text();
            $(comment_div).find(".similar-comment-text").html(text.replace(regex, '<i><b>$&</b></i>'));

            if (comment_div.index() != i) {
              $('.similar-'+comment_type+'-wrapper > div:nth-child('+i+')').after(comment_div);
            }
            continue;
          }

          // Display the full content in a div
          var comment_div = $("<div class='comment'></div>");
          comment_div.addClass("similar-comment");
          comment_div.attr("id", "similar-comment-"+results[i].index);
          var comment_text = $("<span></span>");
          comment_text.addClass("similar-comment-text");
          comment_text.html(commentsData[results[i].index].replace(regex, '<i><b>$&</b></i>'));
          comment_div.append(comment_text);
          if (commentsExtraData[results[i].index].author != "") {
            var author_link = $("<a target='_blank' class='similar-comment-author-link'></a>");
            author_link.attr("href", commentsExtraData[results[i].index].author_url);
            author_link.html(commentsExtraData[results[i].index].author);
            comment_div.append(" - ", author_link);
          }

          // Add new similar comment to after the previous result, in the correct order
          if (i == 0) { // This is the first result to be displayed
            $('.similar-'+comment_type+'-wrapper').prepend(comment_div);
          }
          else {
            // jQuery is stupid and 1-indexes its selectors, thus using i rather i-1
            $('.similar-'+comment_type+'-wrapper > div:nth-child('+i+')').after(comment_div);
          }

        }

        // Remove results that weren't in the top 3
        var selectorString = ".".concat("similar-comment")
                                .concat(":not(")
                                .concat(ids.join())
                                .concat(")");
        $(selectorString).remove();

        if ($(".similar-"+comment_type+"-wrapper").is(":empty")) {
          $(".new-"+comment_type).removeClass("selected");
        }
        else if (!$(".new-"+comment_type).hasClass("selected")) {
          $(".new-"+comment_type).addClass("selected");          
        }

      });
    } catch(err) {
      // fullproof engine throws an error when the only query words are stopwords (or the query is empty).
      // This is ok because there will be 0 similar comments, so just hard code this.

      $(".similar-"+comment_type+"-wrapper").empty();
    }
  };

}
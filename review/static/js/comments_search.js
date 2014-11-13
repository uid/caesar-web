////////////////////////////////////////////////////////////////////////
// Helper methods
////////////////////////////////////////////////////////////////////////  

// Check whether cursor is at the end of the the textentry
function cursorAtEnd($textentry) {
  // getText() found in chunk.js
  var content = getText($textentry);

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
      return true;
    }
  }
  return false;
}

// Select (highlight) the text contained in the div with ID elementId
function selectText(elementId) {
  var doc = document
    , text = doc.getElementById(elementId)
    , range, selection
  ;
  if (doc.body.createTextRange) {
    range = document.body.createTextRange();
    range.moveToElementText(text);
    range.select();
  } else if (window.getSelection) {
    selection = window.getSelection();        
    range = document.createRange();
    range.selectNodeContents(text);
    selection.removeAllRanges();
    selection.addRange(range);
  }
}

// Record how user uses the system in the Caesar log
function logUsage(data) {
  $.ajax({
    type: "POST",
    url: "/log/log/",
    data: data
  });
}

// Clear similarCommentsDB database !important
function clearDatabase(chunk_id) {
  var db;
  if ($.browser.mozilla) {
    indexedDB.deleteDatabase("similarCommentsDB-"+chunk_id);
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

////////////////////////////////////////////////////////////////////////
// Call this function when opening a comment form
////////////////////////////////////////////////////////////////////////  
function setupSimilarComments(comment_type) {

  var ascii_keys = {9: "tab", 13: "return", 37: "left", 38: "up", 39: "right", 40: "down"};

  // Create similar-comment wrapper
  var similar_comment_wrapper = $("<div class='similar-"+comment_type+"-wrapper'></div>");
  $(".new-"+comment_type).after(similar_comment_wrapper);

  // Remove similar-comment feedback from textentry
  function removeFeedback($textentry) {
    $("#feedback").remove();
    $(".bubble").hide();
  }

  function createBubble(commentsData, _callback) {
    $.ajax({
      url: commentsData.highlight_chunk_line_url,
      success: function(response) {
        var $bubble = $("<span class='bubble triangle-border left'></span>").attr("id", "bubble-"+commentsData.comment_id);
        var $syntax = $("<div class='syntax'></div>");
        for (var i in response.chunk_lines) {
          n = response.chunk_lines[i][0];
          chunk_line = response.chunk_lines[i][1];
          staff_code = response.chunk_lines[i][2];
          var $link = $("<a class='chunk-line' target='_blank'></a>").attr(
            {"id": "chunk-"+commentsData.chunk_id,
            "href": "/chunks/view/"+commentsData.chunk_id+"#comment-"+commentsData.comment_id}
          );
          if (!staff_code) {
            $link.addClass("chunk-line-student");
          }
          else {
            $link.addClass("chunk-line-staff");
          }
          var $line = $("<span class='bubble-line'></span>").attr("id", "line-"+commentsData.chunk_id+"-"+n+"-"+response.file_id);
          var $line_number = $("<span class='line-number'></span>").html(n);
          var $line_code = $("<pre class='line-code'></pre>").html(chunk_line);
          $line.append($line_number, $line_code);
          $link.append($line);
          $syntax.append($link);
        }
        $bubble.append($syntax);
        _callback($bubble);
      }
    });
  }

  // Add similar-comment feedback to textentry
  function addFeedback($textentry, $similar_comment, similar_comment_text) {
    var feedback = $("<div id='feedback'></div>");
    feedback.text(similar_comment_text);
    $textentry.append(feedback);
    var comment_id = $similar_comment.attr("id").replace("similar-comment-", "");
    var offset = $similar_comment.offset();
    var width = $similar_comment.outerWidth();
    var height = $similar_comment.height();
    var $bubble = $("#bubble-"+comment_id);
    if ($bubble.length == 0) {
      createBubble($similar_comment.data(), function($bubble) {
        $("body").append($bubble);
        // Triangle center is 16px from top of bubble, with 10px on the top and bottom. I tried getting these values from the CSS but I couldn't find them, so this will have to be a magic number.
        $bubble.offset({"top": offset.top + height/2.0 - 26, "left": offset.left + width + 30});
      });
    }
    else {
      $bubble.show();
      $bubble.offset({"top": offset.top + height/2.0 - 26, "left": offset.left + width + 30});
    }
  }

  // Select the textentry (to show that navigation through similar comments is possible)
  function turnOnSelection() {
    $(".new-"+comment_type).addClass("selected");
  }

  // Deselect the textentry (to show that navigation through similar comments is disabled)
  function turnOffSelection() {
    $(".selected").removeClass("selected");
  }

  // Navigate to the next similar comment in the list
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

  // Navigate to the previous similar comment in the list, or to the textentry if user is at the top of the list
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

  function selectSimilarComment($textentry) {
    feedback_text = $("#feedback").text();
    selectText($textentry.attr("id"));
    $textentry.append("</br>", feedback_text);
    removeFeedback($textentry);
    var comment_id = $(".selected").data().comment_id;
    $(".selected").removeClass("selected");
    $(".similar-"+comment_type+"-wrapper").empty();
    logUsage({
      "event": ascii_keys[event.which],
      "comment_id": comment_id
    });
    $("#hidden-similar-comment").val(comment_id);
  }

  ////////////////////////////////////////////////////////////////////////
  // Listeners
  ////////////////////////////////////////////////////////////////////////  

  // Handle arrow key navigation of textentry box and similar comments
  $("#textentry").on("keydown", function(event) {
    if ($(".similar-"+comment_type+"-wrapper").is(":empty")) {
      return;
    }
    if (event.which in ascii_keys) {
      if (cursorAtEnd($(this))) {
        if (ascii_keys[event.which] == "down" || ascii_keys[event.which] == "right" || ascii_keys[event.which] == "tab") {
          selectNext();
          removeFeedback($(this));
          addFeedback($(this), $(".similar-comment.selected"), $(".similar-comment.selected .similar-comment-text").text());
          var comment_id = $(".selected").data().comment_id;
          logUsage({
            "event": ascii_keys[event.which],
            "comment_id": comment_id
          });
          return false;
        }
        else if (ascii_keys[event.which] == "up" || ascii_keys[event.which] == "left") {
          if ($(".similar-comment.selected").length != 0) {
            selectPrevious();
            removeFeedback($(this));
            if ($(".similar-comment.selected").length != 0) {
              addFeedback($(this), $(".similar-comment.selected"), $(".similar-comment.selected .similar-comment-text").text());
              var comment_id = $(".selected").data().comment_id;
              logUsage({
                "event": ascii_keys[event.which],
                "comment_id": comment_id
              });
            }
            return false;
          }
          else {
            turnOffSelection();
          }
        }
        else if (ascii_keys[event.which] == "return") {
          if ($(".similar-comment.selected").length != 0) {
            selectSimilarComment($(this));
            return false; // Halt the return key propagation because this will delete the selected text!
          }
        }
      }
    }
  });

  // Copy textentry text to hidden form textarea, and perform search
  $("#textentry").on("keyup mouseup", function(event) {
    var $textentry = $(this);
    if ($textentry.text() == "") { // No need to search because textfield is empty
      $textentry.empty();
      turnOffSelection();
      $(".similar-"+comment_type+"-wrapper").empty();
    }
    else if (event.which in ascii_keys || event.type=="mouseup") { // User is navigating
      if (cursorAtEnd($textentry)) {
        if ($(".selected").length == 0 && !$(".similar-"+comment_type+"-wrapper").is(":empty")) {
          turnOnSelection();
        }
      }
      else {
        removeFeedback();
        turnOffSelection();
      }
    }
    else { // User types normal keys (ex. letters/numbers)
      removeFeedback($textentry);
      $(".similar-comment.selected").removeClass("selected");
      var textentry_text = $textentry.text();
      commentSearch.search(textentry_text, comment_type, function() {
        if ($(".similar-"+comment_type+"-wrapper").is(":empty")) {
          turnOffSelection();
        }
        else if (cursorAtEnd($textentry) && $(".selected").length == 0) {
          turnOnSelection();
        }
      });
    }
  });

  $(".similar-"+comment_type+"-wrapper").on("mouseover", ".similar-comment", function() {
    var selected = $(".selected");
    $(this).addClass("selected");
    selected.removeClass("selected");
    removeFeedback($("#textentry"));
    addFeedback($("#textentry"), $(this), $(this).find(".similar-comment-text").text());
    var comment_id = $(".selected").data().comment_id;
    logUsage({
      "event": "mouseover",
      "comment_id": comment_id
    });
  });

  $(".similar-"+comment_type+"-wrapper").on("mouseout", ".similar-comment", function() {
    $(this).removeClass("selected");
    removeFeedback($("#textentry"));
    if (cursorAtEnd($("#textentry"))) {
      turnOnSelection();
    }
  });

  $(".similar-"+comment_type+"-wrapper").on("click", ".similar-comment", function() {
    selectSimilarComment($("#textentry"));
  });

  // When user clicks on the chunks in the bubble next to a similar comment, opens a new tab at that comment
  $(".bubble .syntax .chunk-line").on("click", function() {
    // Get comment id from bubble, whose id is bubble-{{comment.id}}
    var comment_id = $(this).parent().parent().data().comment_id;
    // Get chunk id from chunkline, whose id is chunkline-{{comment.chunk.id}}-line-{{n}}
    var chunk_id = $(this).attr("id").split("-"[1]);
    logUsage({
      "event": "mouseclick",
      "comment_id": comment_id,
      "chunk_id": chunk_id,
    });
  });

  // Remove similar-comment wrapper whenever the user closes a new comment entry box.
  $(".new-"+comment_type).on("remove", function(e) {
    $(".similar-"+comment_type+"-wrapper").remove();
    $(".bubble").hide();
  });

}

////////////////////////////////////////////////////////////////////////
// Comment Search Class
////////////////////////////////////////////////////////////////////////  
var commentSearch = new function() {

  var dbName, commentsSearchEngine, commentsData;

  var initializer = function(injector, callback) {
    var commentsData_copy = [];
    for (var i in commentsData) {
      commentsData_copy.push(commentsData[i].comment);
    }
    var synchro = fullproof.make_synchro_point(callback, commentsData_copy.length-1);
    var values = [];
    for (var i=0;i<commentsData_copy.length; ++i) {
      values.push(i);
    }
    injector.injectBulk(commentsData_copy, values, callback);
  }

  var engineReady = function(b) {
    if (!b) {
      console.log("Can't load the search engine!");
    }
  }

  this.init = function(commentsData_, chunk_id) {

    dbName = "similarCommentsDB-"+chunk_id;
    commentsSearchEngine = new fullproof.ScoringEngine();
    commentsData = commentsData_;
    var index1 = new fullproof.IndexUnit(
      "normalindex",
      new fullproof.Capabilities().setStoreObjects(false).setUseScores(true).setDbName(dbName).setComparatorObject(fullproof.ScoredEntry.comparatorObject).setDbSize(8*1024*1024),
      new fullproof.ScoringAnalyzer(fullproof.normalizer.to_lowercase_nomark, fullproof.english.stopword_remover, fullproof.normalizer.remove_duplicate_letters),
      initializer
    );

    var index2 = new fullproof.IndexUnit(
      "stemmedindex",
      new fullproof.Capabilities().setStoreObjects(false).setUseScores(true).setDbName(dbName).setComparatorObject(fullproof.ScoredEntry.comparatorObject).setDbSize(8*1024*1024),
      new fullproof.ScoringAnalyzer(fullproof.normalizer.to_lowercase_nomark, fullproof.english.porter_stemmer),
      initializer
    );

    commentsSearchEngine.open([index1,index2], fullproof.make_callback(engineReady, true), fullproof.make_callback(engineReady, false));

  };

  this.search = function(value, comment_type, _callback) {

    // Create regular expression for highlighting query words
    var split_string = "zDVJRqVs";
    var wordset = value.replace(/\n|\r|\s/g, split_string).split(split_string);
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
                "bag_of_words": regex.exec(commentsData[e.value].comment),
              });              
            }
          });
        }

        // Sort results from highest score to lowest score
        results.sort(function(a,b) { return b.score - a.score; });

        var ids = [];

        // Display only the top 3 results.
        for (var i=0; i<Math.min(results.length, 3); i++) {

          ids.push('#similar-comment-'+commentsData[results[i].index].comment_id);

           // Check whether this result is already displayed
          if ($('#similar-comment-'+commentsData[results[i].index].comment_id).length != 0) {
            var comment_div = $('#similar-comment-'+commentsData[results[i].index].comment_id);
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
          comment_div.attr("id", "similar-comment-"+commentsData[results[i].index].comment_id);
          var comment_text = $("<span></span>");
          comment_text.addClass("similar-comment-text");
          comment_text.html(commentsData[results[i].index].comment.replace(regex, '<i><b>$&</b></i>'));
          comment_div.append(comment_text);
          var author_link = $("<a target='_blank' class='similar-comment-author-link'></a>");
          author_link.attr("href", commentsData[results[i].index].author_url);
          author_link.html(commentsData[results[i].index].author);
          comment_div.append(" - ", author_link);
          comment_div.data(commentsData[results[i].index]);

          // Add new similar comment to after the previous result, in the correct order
          if (i == 0) { // This is the first result to be displayed
            $('.similar-'+comment_type+'-wrapper').prepend(comment_div);
          }
          else {
            // jQuery 1-indexes its selectors, thus using i rather i-1
            $('.similar-'+comment_type+'-wrapper > div:nth-child('+i+')').after(comment_div);
          }

        }

        // Remove results that weren't in the top 3
        var selectorString = ".".concat("similar-comment")
                                .concat(":not(")
                                .concat(ids.join())
                                .concat(")");
        $(selectorString).remove();

        _callback();

      });
    } catch(err) {
      // fullproof engine throws an error when the only query words are stopwords (or the query is empty).
      // This is ok because there will be 0 similar comments, so just hard code this.

      $(".similar-"+comment_type+"-wrapper").empty();

    }

  };

}
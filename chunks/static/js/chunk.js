var model = new function() {
    var self = this;
    var listeners = {};
    
    self.addListener = function(eventName, listener) {
        if (!listeners[eventName]) {
            listeners[eventName] = [];
        }
        listeners[eventName].push(listener);
    };

    var fireEvent = function(eventName) {
        var args = Array.prototype.slice.call(arguments);
        args.shift();
    
        if (listeners[eventName]) {
            $.each(listeners[eventName], function(index, listener) {
                listener.apply(self, args);
            });
        }
    };

    self.comments = [];
    self.task = {
        status: caesar.state.taskStatus 
    };

    var startTask = function() {
        if (self.task.status === 'O') {
            self.task.status = 'S';
            fireEvent('taskStarted');
        }
    };
    self.addListener('commentAdded', startTask);
    self.addListener('commentVoted', startTask);

    self.computeIndex = function(start, end, isReply, parentId) {
        var target;
        if (!isReply) {
            target = self.comments.length;
            $.each(self.comments, function(index, comment) {
                if ((start == comment.start && end > comment.end) ||
                        start < comment.start) {
                    target = index;
                    return false;
                }
            });
        } else {
            // iterate backwards over the comments
            for (var i = self.comments.length - 1; i >= 0; i--) {
                var comment = self.comments[i];
                // find the parent or another reply in the same thread
                if (comment.id == parentId || comment.parentId == parentId) {
                    target = i + 1;
                    break;
                }
            }
        }
        return target;
    };

    self.addComment = function(comment) {
        var target = self.computeIndex(comment.start, comment.end, 
                                       comment.isReply, comment.parentId);
        self.comments.splice(target, 0, comment);
        fireEvent('commentAdded', comment);
    };

    self.addCommentFromDOM = function(elt) {
        var idSplit = elt.id.split('-');
        var isReply = $(elt).hasClass('comment-reply') 
        var comment =  { 
            id: parseInt(idSplit[1]), 
            start: parseInt(idSplit[2]), 
            end: parseInt(idSplit[3]),
            chunk: parseInt(idSplit[4]),
            file: parseInt(idSplit[5]),
            isReply: isReply,
            parentId: isReply ? parseInt(
                    $(elt).attr('class').match(/parent-(\d+)/)[1]) : null,
            elt: elt 
        };
        self.addComment(comment);
        return comment;
    };

    self.removeComment = function(comment) {
        var index = self.comments.indexOf(comment);
        if (index != -1) {
            self.comments.splice(index, 1);
            fireEvent('commentRemoved', comment);    
        }
    };

    self.voteComment = function(comment, voteValue) {
        fireEvent('commentVoted', comment, voteValue);
    };

    self.unvoteComment = function(comment) {
        fireEvent('commentUnvoted', comment);
    };

};


window.isSelecting = false;

function showCommentForm(startLine, endLine, chunkId, fileId) {
    clearSpecial();
    $.get(caesar.urls.new_comment, 
        { start: startLine, end: endLine, chunk: chunkId},
        function(data) {
            $('.new-comment').remove();
            $('.reply-form').parent().remove();
            // find the appropriate place to insert the form
            var added = false;
            var elt = $(data);
            var index = model.computeIndex(startLine, endLine);
            $.each(model.comments, function(index, comment) {
                if (comment.chunk == chunkId && ((startLine == comment.start && endLine > comment.end)
                    || startLine < comment.start)) {
                    $(comment.elt).before(elt);                        
                    added = true;
                    return false;
                }
            });
            if (!added) {
                $('.file-'+fileId).append(elt);
            }
            // construct a fake "comment" boundary object to pass in
            var commentElt = elt.filter('.comment').get(0);
            scrollCodeTo({
                start: startLine, 
                end: endLine, 
                elt: commentElt,
                chunk: chunkId,
                file: fileId
            }, true, function() {
                $('#textentry').focus();
            }); 
        }
    );
};

function showEditForm(commentId, startLine, endLine, chunkId, fileId, comment) {
    $.get(caesar.urls.edit_comment, 
        { comment_id: commentId},
        function(data) {
            $(comment.elt).hide(); 
            $('.reply-form').parent().remove();
            //if reply
            var isReply = $(comment.elt).hasClass('comment-reply')
            var commentElt;
            if (isReply){
                commentElt = $(data).insertAfter(comment.elt);
            } else{
                // find the appropriate place to insert the form
                var added = false;
                var elt = $(data);
                var index = model.computeIndex(startLine, endLine);
                $.each(model.comments, function(index, comment) {
                    if (comment.chunk == chunkId && ((startLine == comment.start && endLine > comment.end)
                        || startLine < comment.start)) {
                        $(comment.elt).before(elt);
                        added = true;
                        return false;
                    }
                });
                if (!added) {
                    $('.file-'+fileId).append(elt);
                    console.log("uh oh");
                }
                // construct a fake "comment" boundary object to pass in
                commentElt = elt.filter('.comment').get(0);
            }
            scrollCodeTo({
                start: startLine, 
                end: endLine, 
                elt: commentElt,
                chunk: chunkId,
                file: fileId
            }, true, function() {
                $('#textentry').focus();
            }); 
        }
    );
};

function highlightCommentLines(comment) {
    // highlight corresponding code lines
    for (var i = comment.start; i <= comment.end; i++) {
        $('#line-' + comment.chunk + '-' + i + '-' + comment.file).addClass('highlighted');            
    }
};

function unhighlightCommentLines() {
    $('.line').removeClass('highlighted');
};

function collapseComment(comment) {
    $(comment.elt).stop(true, true)
            .switchClass('expanded', 'collapsed', 'fast');
    $('.parent-' + comment.id).stop(true, true)
            .switchClass('expanded', 'collapsed', 'fast');
};

function expandComment(comment) {
    $(comment.elt).stop(true, true)
            .switchClass('collapsed', 'expanded', 'fast');
    $('.parent-' + comment.id).stop(true, true)
            .switchClass('collapsed', 'expanded', 'fast');
};

function collapseAllComments() {
    $('.comment').stop(true, true).switchClass('expanded', 'collapsed', 'fast');
};

function expandAllComments() {
    $('.comment').stop(true, true).switchClass('collapsed', 'expanded', 'fast');
};

function collapseAllAutoComments() {
    $('.comment-auto').stop(true, true).switchClass('expanded', 'collapsed', 'fast');
};

function expandAllAutoComments() {
    $('.comment-auto').stop(true, true).switchClass('collapsed', 'expanded', 'fast');
};

function scrollCodeTo(comment, doScroll, callback) {

    history.replaceState(history.state, "", "#comment-" + comment.id)

    if (doScroll === undefined) {
            doScroll = true;
        }
        if (callback === undefined) {
            callback = function() { return; };
        }
        var SCROLL_THRESHOLD = 75;
        var targetLine = $('#chunk-' + comment.chunk + '-line-' + comment.start);
        var commentTop = $(comment.elt).offset().top;
        var commentHeight = $(comment.elt).height();
        var yDelta = targetLine.offset().top - commentTop ;

        // Wraps the callback so it is only executed the nth time it is called
        // This guarantees that the callback is called exactly once and after all
        // animations have run.
        // FIXME Because of the way this code is structured, it is extremely 
        // easy to forget to call the callback in all cases to guarantee execution.
        function wrapCallback(f, n) {
            var i = 0;
            return function() {
                if (i + 1 == n) {
                    return f();
                } else {
                    i++;
                }
            };
        };

        var cb = wrapCallback(callback, 3);
        $('.file-'+comment.file).animate({
            top: '+=' + yDelta
        }, { duration: 500, queue: false, easing: 'easeInOutQuad', complete: cb });

        if (!doScroll) {
            cb(); cb();
            return;
        }

        var windowHeight = $(window).height();
        if (commentTop + yDelta + commentHeight >
                windowHeight + $(window).scrollTop()) {
            $('html,body').animate({
                scrollTop: commentTop - windowHeight + 
                    commentHeight + yDelta + SCROLL_THRESHOLD
            }, { duration: 500, queue: false, easing: 'easeInOutQuad',
                 complete: cb }); 
        } else if (commentTop + yDelta < $(window).scrollTop()) {
            $('html,body').animate({
                scrollTop: commentTop + yDelta - SCROLL_THRESHOLD
            }, { duration: 500, queue: false, easing: 'easeInOutQuad', 
                 complete: cb }); 
        } else {
            cb(); cb();
        }

        return yDelta;
};

function resetScroll() {
    $('.files').animate({
        top: 0
    }, { duration: 500, queue: false });
    clearSpecial();

};

window.clearSelection = function() {
    isSelecting = false;
    $('.line').removeClass('ui-selected');
    $('.new-comment').remove();
    $('.reply-form').parent().remove();
};

function drawCommentMarker(comment) {
    if (!$('#chunk-' + comment.chunk +'-line-' + comment.start).has('.comment-marker').size()) {
        $('<span></span>')
          .prependTo('#chunk-' + comment.chunk + '-line-' + comment.start)
          .addClass('comment-marker')
          .data('count', 1)
          .click(function(e) { 
              scrollCodeTo(comment);
              checkIfSpecial(comment);
              $.each(model.comments, function(index, innerComment) {
                  if (innerComment.start === comment.start) {
                      expandComment(innerComment); //expands the related comments when the marker is clicked.
                  }
              });
          });
    } else {
        var marker = $('#chunk-' + comment.chunk + '-line-' + comment.start)
                .children('.comment-marker');
        var count = marker.data('count') + 1;
        marker.data('count', count);
        marker.text(count);
    }
}

function removeCommentMarker(comment) {
    var marker = $('#chunk-' + comment.chunk + '-line-' + comment.start).children('.comment-marker');
    if (marker.data('count') <= 1) {
        marker.remove();
    } else {
        var count = marker.data('count') - 1;
        marker.data('count', count);
        marker.text(count);
    }
}

function drawCommentButtons(comment) {
    $('.reply-button', comment.elt).button({
        icons: { primary: 'ui-icon-reply', secondary: null },
        text: true
    });
    $('.delete-button', comment.elt).button({
        icons: { primary: 'ui-icon-delete', secondary: null },
        text: false
    });
    $('.edit-button', comment.elt).button({
        icons: { primary: 'ui-icon-edit', secondary: null },
        text: false
    });
}

function clearSpecial() {
    $('.comment-text').removeClass('highlight');
    $('#voteup').removeClass('highlight');
    $('#votedown').removeClass('highlight');    
    $('.line').removeClass('highlight');    
}

function checkIfSpecial(comment) {  
    var myFile = document.location.toString();
    if (myFile.match('#')) { // the URL contains an anchor
      var myAnchor = myFile.split('#')[1];
      var highlight_type = myAnchor.split('-')[0];
      var highlight_id = myAnchor.split('-')[1];
      

      
      // highlight actually special one
      if (comment.id == highlight_id){     
            // clear previous special guys
              clearSpecial(comment);
          if (highlight_type == "comment"){
              $('#comment-text-'+ highlight_id).addClass('highlight');
          }
          if (highlight_type == "voteup"){
              $('#voteup-' + highlight_id).addClass('highlight');
          }
          if (highlight_type == "votedown"){
              $('#votedown-' + highlight_id).addClass('highlight');
          }
          //highlight comment lines
          for (var i = comment.start; i <= comment.end; i++) {
              $('#line-' + comment.chunk + '-' + i + '-' + comment.file).addClass('highlight');
          }
            return true;
       }
    }
    else{
        $('#highlight-comment-text-'+ comment.id).addClass('highlight');
        if ($('#highlight-comment-text-'+ comment.id).hasClass('highlight')){
            //highlight comment lines
            for (var i = comment.start; i <= comment.end; i++) {
                $('#line-' + comment.chunk + '-' + i + '-' + comment.file).addClass('highlight');
            }
        }
    }
    return false;
}

function attachCommentHandlers(comment) {
    $('.comment-header', comment.elt).click(function() {
        if ($(comment.elt).hasClass('collapsed')) {
            expandComment(comment);
        } else {
            collapseComment(comment);
        }
        return false;
    });

    $(comment.elt).click(function() {
        if ($(comment.elt).hasClass('collapsed')) {
            expandComment(comment);
        } else {
            scrollCodeTo(comment);
            checkIfSpecial(comment)
        }
    });

    if (caesar.state.fullView) {
        //reply button
        $('.reply-button', comment.elt).click(function() {
            clearSpecial();
            $.get(caesar.urls.reply, 
                { parent: comment.id }    ,
                function(data) {
                    $('.reply-form').parent().remove();
                    clearSelection();

                    // find the appropriate place to insert the form
                    var previousComment = comment.elt;
                    var lastReply = $(comment.elt)
                            .nextUntil('.comment:not(.comment-reply)').last();
                    if (lastReply.length) {
                        previousComment = lastReply;
                    }

                    var replyElt = $(data).insertAfter(previousComment);
                    scrollCodeTo({
                        start: comment.start, 
                        end: comment.end, 
                        chunk: comment.chunk,
                        file: comment.file,
                        elt: replyElt.get(0) 
                    }, true, function() { 
                        $('#textentry').focus();
                    });
                }
            );
            return false;
        });

        // delete button
        $('.delete-button', comment.elt).click(function() {
            clearSpecial();
            $.get(caesar.urls.delete, {
                comment_id: comment.id
            }, function(data) {
                $("#comment-text-"+comment.id).text("[deleted]");
            });
            return false;
        });
        
        // edit button
        $('.edit-button', comment.elt).click(function() {
            clearSpecial();
                showEditForm(comment.id, comment.start, comment.end, comment.chunk, comment.file, comment);
        });
        
        $('.vote-buttons.enabled .vote', comment.elt).click(function(e) {
            var button = this;
            var isUp = $(this).hasClass('up');
            if (!$(this).is('.selected')) {
                var value = isUp ? 1 : -1;
                $.post(caesar.urls.vote, {
                    comment_id: comment.id,
                    value: value,
                }, function(data) {
                    $(button).addClass('selected');
                    // deselect the other vote button if it is selected
                    var otherButton = isUp ? $(button).nextAll('.vote') :
                        $(button).prevAll('.vote');
                    otherButton.removeClass('selected');
                    $('.comment-votes .vote.up', comment.elt)
                        .text(data.upvote_count);
                        // .effect('highlight', {queue: false}, 1000);
                    $('.comment-votes .vote.down', comment.elt)
                        .text(data.downvote_count);
                        // .effect('highlight', {queue: false}, 1000);
                    model.voteComment(comment, value);
                },"json");
            } else {
                $.post(caesar.urls.unvote, {
                    comment_id: comment.id
                }, function(data) {
                    $(button).removeClass('selected');
                    $('.comment-votes .vote.up', comment.elt)
                        .text(data.upvote_count);
                        // .effect('highlight', {queue: false}, 1000);
                    $('.comment-votes .vote.down', comment.elt)
                        .text(data.downvote_count);
                        // .effect('highlight', {queue: false}, 1000);
                    model.unvoteComment(comment);
                },"json");
            }
            return false;
        });
    }

    // mouseover behavior
    $(comment.elt).mouseover(function() {
        highlightCommentLines(comment);
    });
    $(comment.elt).mouseout(function() {
        unhighlightCommentLines();
    });

}

model.addListener('commentAdded', function(comment) {
    drawCommentMarker(comment);
    if (caesar.state.fullView) {
        drawCommentButtons(comment);
    }
    attachCommentHandlers(comment);
    if (checkIfSpecial(comment)) {
        scrollCodeTo(comment);
        checkIfSpecial(comment);
    }
});

model.addListener('commentRemoved', function(comment) {
    $(comment.elt).remove();        
    $('.parent-' + comment.id).remove();
    $('.line').removeClass('highlighted');            
    removeCommentMarker(comment);
    resetScroll();
});

model.addListener('taskStarted', function() {
    $('#done-button').removeAttr('disabled');
});

// Get text content of contenteditable div (without HTML attributes)
function getText($textentry) {
  var $textentry_clone = $textentry.clone();
  if ($textentry_clone.find("#feedback").length != 0) {
    $textentry_clone.find("#feedback").remove();
  }

  var content = $("<pre />").html($textentry_clone.html());
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
  return content;
}

$(document).ready(function() {

    $('.comment').each(function() { 
        model.addCommentFromDOM(this);
    });

    // Clear the selected lines if the user clicks anywhere except the comment form
    $('body').mousedown(function(e) {
        if ($(e.target).is('.new-comment *') || $(e.target).is('.new-reply *') || $(e.target).is('.similar-comment *')) {
            return true;
        }
        if ($('.new-comment #textentry').val() || $('.new-reply #textentry').val()) {
            return false;
        }
        clearSelection();
        if (!$(e.target).is('.comment *, .chunk-line *')) {
            resetScroll();
        }
        return true;
    });

    if (caesar.state.fullView) {
        $('div#chunk-display').selectable({
            filter: '.line',
            cancel: '.comment-marker',
            start: function(event, ui) {
                isSelecting = true;
            },
            stop: function(event, ui) {
                var startLine = Number.MAX_VALUE;
                var endLine = Number.MIN_VALUE;
                var chunkId = null;
                var fileId = null;
                $('.line.ui-selected').each(function(i) {
                    var n = parseInt($(this).attr('id').split('-')[2]);
                    endLine = Math.max(endLine, n);
                    startLine = Math.min(startLine, n);
                    chunkId = parseInt($(this).attr('id').split('-')[1]);
                    fileId = parseInt($(this).attr('id').split('-')[3])
                });
                if (chunkId == null) {
                    return; // no lines selected, don't show the form
    	    }
                showCommentForm(startLine, endLine, chunkId, fileId);
            }
        });
    }

    // Save content to hidden textarea. CRITICAL so that form is saved.
    function saveTextToForm() {
        var content = getText($("#textentry"));
        $("#hidden-textarea").val(content);
        console.log(content);
    }

    $('#new-comment-form').live('submit', function() {
        saveTextToForm();
        var dataString = $(this).serialize();
        $.post(caesar.urls.new_comment, dataString, function(data) {
            var newNode = $(data);
            $('.new-comment').replaceWith(newNode);
            model.addCommentFromDOM(newNode.get(0));
            newNode.effect('highlight', {}, 2000);
            resetScroll();
            clearSelection();
        });
        return false;
    });

    $('#edit-comment-form').live('submit', function() {
        saveTextToForm();
        var dataString = $(this).serialize();
        $.post(caesar.urls.edit_comment, dataString, function(data) {
            var newNode = $(data);
            $('.new-comment').replaceWith(newNode);
            $('.new-reply').replaceWith(newNode);
            //remove the one that's hiding
            var idSplit = newNode.get(0).id.split('-');
            var comment_id = parseInt(idSplit[1]);
            $.each(model.comments, function(index, comment) {
                if (comment != undefined && comment.id == comment_id){
                    model.removeComment(comment);
                }
            });
            model.addCommentFromDOM(newNode.get(0));
            newNode.effect('highlight', {}, 2000);
            resetScroll();
            clearSelection();
        });
        return false;
    });

    $('#reply-comment-form').live('submit', function() {
        saveTextToForm();
        var dataString = $(this).serialize();
        $.post(caesar.urls.reply, dataString, function(data) {
            var newNode = $(data);
            $('.new-reply').replaceWith(newNode);
            model.addCommentFromDOM(newNode.get(0));
            newNode.effect('highlight', {}, 2000);
            resetScroll();
            clearSelection();
        });
        return false;
    });

    $('#cancel-button').live('click', function() {
        resetScroll();
        clearSelection();
        $.each(model.comments, function(index, comment) {
            $(comment.elt).show();
        });
    });

    $('#cancel-reply-button').live('click', function() {
        resetScroll();
        $('.reply-form').parent().remove();
        $.each(model.comments, function(index, comment) {
            $(comment.elt).show();
        });
    });

    var toggleCommentsText = {
        collapse: 'Collapse all comments', 
        expand: 'Expand all comments'
    };
    $('#toggle-comments-button').data('state', 'collapse');
    $('#toggle-comments-button').click(function() {
        var state = $(this).data('state');
        if (state === 'collapse') {
            collapseAllComments();
            state = 'expand';
        } else {
            expandAllComments();
            state = 'collapse';
        }
        $(this).text(toggleCommentsText[state]).data('state', state);
    });

    var toggleAutoCommentsText = {
        collapse: 'Collapse all checkstyle comments', 
        expand: 'Expand all checkstyle comments'
    };
    $('#toggle-auto-comments-button').data('state', 'collapse');
    $('#toggle-auto-comments-button').click(function() {
        var state = $(this).data('state');
        if (state === 'collapse') {
            collapseAllAutoComments();
            state = 'expand';
        } else {
            expandAllAutoComments();
            state = 'collapse';
        }
        $(this).text(toggleAutoCommentsText[state]).data('state', state);
    });

    var toggleInstructionsText = {
        visible: 'Hide instructions', 
        hidden: 'Show instructions' 
    };
    var instructionsState = $.cookie('instructionsState') || 'visible';

    if (instructionsState === 'visible') {
        $('#instructions-text').show();
    } else {
        $('#instructions-text').hide();
    }
    $('#toggle-instructions-button')
            .text(toggleInstructionsText[instructionsState]);

    $('#toggle-instructions-button').click(function() {
        if (instructionsState === 'visible') {
            $('#instructions-text').slideUp(400);
            instructionsState = 'hidden';
        } else {
            $('#instructions-text').slideDown(400);
            instructionsState = 'visible';
        }
        $.cookie('instructionsState', instructionsState);
        $(this).text(toggleInstructionsText[instructionsState]);
    });

    $('.dropdown-link').click(function() {
        var menu = $(this).next('.dropdown-menu');
        var position = $(this).position();
        var height = $(this).outerHeight();
        menu.css({ top: position.top + height, left: position.left });
        menu.slideDown(400);
        return false;
    });

    $('body').click(function() {
        $('.dropdown-menu').slideUp(400); 
    });

    $('pre.line-code').each(function(i,e){$(this).prepend($(this).prev());$(this).prev().remove();})

});

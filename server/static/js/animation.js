$(document).ready(function () {
  update_indicator();

  $('.tab-title').click(function () {
    if ($(this).siblings('.tab-content').is(":hidden")) {
      $(this).children('i').removeClass('fa-angle-left');
      $(this).children('i').addClass('fa-angle-down');
    } else {
      $(this).children('i').removeClass('fa-angle-down');
      $(this).children('i').addClass('fa-angle-left');
    }
    $(this).siblings('.tab-content').slideToggle('fast');
  });

  window.onscroll = function () { scrollFunction() };

});


function update_indicator() {
  $('.tab-content').each(function () {
    if ($(this).hasClass('hidden')) {
      $(this).removeClass('hidden');
      $(this).siblings('.tab-title').children('i').addClass('fa-angle-left');
      $(this).siblings('.tab-title').children('i').removeClass('fa-angle-down');
    } else {
      $(this).slideToggle('fast');
      $(this).siblings('.tab-title').children('i').removeClass('fa-angle-left');
      $(this).siblings('.tab-title').children('i').addClass('fa-angle-down');
    }
  });
}


//Get the button:

// When the user scrolls down 20px from the top of the document, show the button

function scrollFunction() {
  mybutton = document.getElementById("goto_top_button");
  if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    mybutton.style.display = "block";
  } else {
    mybutton.style.display = "none";
  }
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
  document.body.scrollTop = 0; // For Safari
  document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}
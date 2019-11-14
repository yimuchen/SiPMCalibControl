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

});


function update_indicator(){
  $('.tab-content').each( function(){
    if($(this).hasClass('hidden')){
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
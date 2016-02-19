jQuery(document).ready(function () {

    // Hint visibility toggling
    Array.prototype.forEach.call(jQuery(".problem"), function(prob) {
        jQuery(".hint-button", prob).on('click', function (event) {
            jQuery('.hint-content', prob).toggle('show');
        });
    });

    // Enable AJAX for flag submissions
    Array.prototype.forEach.call(jQuery(".problem"), function(prob) {
      var prob_form = jQuery(".flag-submit", prob);
      prob_form.on('submit', function (event) {
        event.preventDefault();
        
        submit_flag(prob.id, prob_form.serialize());
      });
    });

});

function submit_flag(id, data) {
  console.log(data);
}

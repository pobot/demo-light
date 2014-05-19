$(document).ready(function() {
    Date.prototype.toHHMMSS = function () {
        var hours   = this.getHours();
        var minutes = this.getMinutes();
        var seconds = this.getSeconds();

        if (hours   < 10) {hours   = "0"+hours;}
        if (minutes < 10) {minutes = "0"+minutes;}
        if (seconds < 10) {seconds = "0"+seconds;}
        var time    = hours+':'+minutes+':'+seconds;
        return time;
    }
    function update_clock() {
        $("#clock").text(new Date().toHHMMSS());
    }
    update_clock();
    setInterval(update_clock, 1000);

    $.extend($.validator.messages, {
        required: "Ce champ est obligatoire",
        digits: "Entrez une valeur entière positive ou nulle",
        min: "Entrez une valeur supérieure ou égale à {0}",
        max: "Entrez une valeur inférieure ou égale à {0}"
    });

    $.validator.setDefaults({
        highlight: function(element) {
            $(element).closest('.form-group').addClass('has-error');
        },
        unhighlight: function(element) {
            $(element).closest('.form-group').removeClass('has-error');
        },
        errorElement: 'span'
    });


});
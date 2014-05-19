$(document).ready(function() {
    'use strict';

    var bulb_on = false;
    var img_bulb = $("img#bulb");
    var sampler = null;
    var img_ball = $("img#ball");
    var measure_display = $("#measure-display");
    var measure = $("#current");

    function activate_light_source(status) {
        $.ajax({
            url: document.location.href + "/light",
            data: {
                "status": status ? "1" : "0"
            },
            method: "POST",
            success: function() {
                img_bulb.attr("src", "/img/bulb-" + (status ? "on" : "off") + ".png");
                $("button.bulb-control").toggleClass("disabled");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                jError(
                    "Erreur imprévue : <br>" + errorThrown,
                    {
                        HideTimeEffect: 500
                    }
                );
            }
        });
    }

    function stop_sampling() {
        if (sampler) {
            $(".animated").fadeOut();
            measure_display.addClass("invisible");
            clearInterval(sampler);
            sampler = null;
            $("button.exp-control").toggleClass('disabled');

            activate_light_source(false);
        }
    }

    function get_sample(detection_active) {
        $.ajax({
            url: document.location.href + "/1",
            dataType: "json",
            success: function(data) {
                measure.text(data.current.toFixed(3));
                measure_display.removeClass("invisible");
                if (detection_active) {
                    if (data.detection) {
                        img_ball.fadeIn(300);
                    } else {
                        img_ball.fadeOut(300);
                    }
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                jError(
                    "Erreur mesure : <br>" + errorThrown,
                    {
                        HideTimeEffect: 500
                    }
                );
                stop_sampling();
            }
        });
    }

    function activate_sampler(detection_active) {
        if (!sampler) {
            if (detection_active) {
                activate_light_source(true);
            }
            sampler = setInterval(function() {
                get_sample(detection_active);
            }, 1000);
            $("button.exp-control").toggleClass('disabled');
        }
    }

    $("button#bulb-on").click(function(){
        activate_light_source(true);
    });

    $("button#bulb-off").click(function(){
        activate_light_source(false);
    });

    $("button#sampling-on").click(function(){
        activate_sampler(false);
    });

    $("button#detection-on").click(function(){
        activate_sampler(true);
    });

    $("button#experiment-end").click(stop_sampling);

    $(window).unload(stop_sampling);
});
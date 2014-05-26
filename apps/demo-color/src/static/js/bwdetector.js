$(document).ready(function() {
    'use strict';

    var img_bulb = $("img#bulb");
    var sampler = null;
    var img_ball = $("img#ball");
    var measure_display = $("#measure-display");
    var measure = $("#current");

    function set_light_source(status) {
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
            clearInterval(sampler);
            sampler = null;

            img_ball.attr("src", "/img/ball-none.png");
            measure_display.addClass("invisible");
            $("button.exp-control").toggleClass('disabled');

            set_light_source(false);
        }
    }

    function get_sample(detection_active) {
        $.ajax({
            url: document.location.href + "/sample",
            dataType: "json",
            success: function(data) {
                measure.text(data.current.toFixed(3));
                measure_display.removeClass("invisible");
                if (detection_active) {
                    img_ball.attr("src", "/img/ball-" + data.color + ".png");
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
                set_light_source(true);
            }
            sampler = setInterval(function() {
                get_sample(detection_active);
            }, 1000);
            $("button.exp-control").toggleClass('disabled');
        }
    }

    $("button#bulb-on").click(function(){
        set_light_source(true);
    });

    $("button#bulb-off").click(function(){
        set_light_source(false);
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
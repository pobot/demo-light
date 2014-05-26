$(document).ready(function() {
    'use strict';

    var img_bulb = $("img#bulb");
    var sampler = null;
    var img_ball = $("img#ball");
    var measure = $("#current");

    function update_meter(value) {
        measure.text(value.toFixed(3));
    }

    function update_bulb(status) {
        img_bulb.attr("src", "/img/bulb-east-" + (status ? "on" : "off") + ".png");
    }

    function set_light_source(status) {
        $.ajax({
            url: document.location.href + "/light",
            data: {
                "status": status ? "1" : "0"
            },
            method: "POST",
            success: function() {
                update_bulb(status);
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
            update_meter(0);
            clearInterval(sampler);
            sampler = null;
            $("button.exp-control").toggleClass('disabled');

            set_light_source(false);
        }
    }

    function get_sample(detection_active) {
        $.ajax({
            url: document.location.href + "/sample",
            dataType: "json",
            success: function(data) {
                update_meter(data.current);
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

    update_meter(0);
    update_bulb(false);
});
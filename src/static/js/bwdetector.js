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
        img_bulb.attr("src", "/img/bulb-south-" + (status ? "on" : "off") + ".png");
    }

    function set_light_source(status) {
        $.post(
            document.location.href + "/light", {"status": status ? "1" : "0"}
        ).done(function() {
            update_bulb(status);
            if (status) {
                $("button#bulb-on").addClass("disabled");
                $("button#bulb-off").removeClass("disabled");
            } else {
                $("button#bulb-off").addClass("disabled");
                $("button#bulb-on").removeClass("disabled");
            }
        }).fail(function(jqXHR, textStatus, errorThrown) {
            jError(
                "Erreur imprévue : <br>" + errorThrown,
                {
                    HideTimeEffect: 500
                }
            );
        });
    }

    function stop_sampling() {
        if (sampler) {
            clearInterval(sampler);
            sampler = null;

            img_ball.attr("src", "/img/ball-none.png");
            update_meter(0);
            $("button.exp-control").toggleClass('disabled');

            set_light_source(false);
        }
    }

    function get_sample(analyze_sample) {
        $.getJSON(
            document.location.href +  (analyze_sample ? "/analyze" : "/sample")
        ).done(function(data) {
            update_meter(data.current);
            if (analyze_sample) {
                img_ball.attr("src", "/img/ball-" + data.color + ".png");
            }
        }).fail(function(jqXHR, textStatus, errorThrown) {
            jError(
                "Erreur mesure : <br>" + errorThrown,
                {
                    HideTimeEffect: 500
                }
            );
            stop_sampling();
        });
    }

    function activate_sampler() {
        if (!sampler) {
            sampler = setInterval(function() {
                get_sample(false);
            }, 1000);
            $("button.exp-control").toggleClass('disabled');
        }
    }

    function activate_analyzer() {
        if (!sampler) {
            $.getJSON(document.location.href + "/status")
            .done(function(result) {
                if (result.calibrated) {
                    set_light_source(true);
                    sampler = setInterval(function () {
                        get_sample(true);
                    }, 1000);
                    $("button.exp-control").toggleClass('disabled');
                } else {
                    jError("Le détecteur doit avoir été calibré avant.");
                }
            });
        }
    }

    $("button#bulb-on").click(function(){
        set_light_source(true);
    });

    $("button#bulb-off").click(function(){
        set_light_source(false);
    });

    $("button#sampling-on").click(function(){
        activate_sampler();
    });

    $("button#detection-on").click(function(){
        activate_analyzer();
    });

    $("button#experiment-end").click(stop_sampling);

    $(window).unload(function(){
        stop_sampling();
        // ensure light is turned off
        set_light_source(false);
    });

    update_meter(0);
    update_bulb(false);
});
$(document).ready(function() {
    'use strict';

    var OFF = 0;
    var RED = 1;
    var GREEN = 2;
    var BLUE = 3;
    var CYCLE_START = RED;
    var CYCLE_END = BLUE;

    var LIGHT_COLOR_CODES = ['0', 'r', 'g', 'b']
    var COLOR_NAMES = ["off", "red", "green", "blue"];


    var img_bulb = $("img#bulb");
    var img_ball = $("img#ball");
    var measure = $("#current");

    var measure_display_simple = $("#measure-display");
    var measure_display_rgb = $("#measure-rgb-display");
    var bar_graphs_container = $("#color-decomp-bargraphs");

    var bar_graphs = [
        $("div#decomp-red"),
        $("div#decomp-green"),
        $("div#decomp-blue")
    ];

    var sampler_timer = null;
    var analyzer_timer = null;
    var stop_requested = false;

    function update_meter(value) {
        measure.text(value.toFixed(3));
    }

    function update_rgb_meter(color, value) {
        $("div#" + color + " #current").text(value.toFixed(3));
    }

    function clear_meters() {
        $("div.measure-display span#current").text("0.000");
    }

    function update_bulb(color) {
        img_bulb.attr("src", "/img/bulb-south-" + COLOR_NAMES[color] + ".png");
    }

    function enable_activation_buttons(enable) {
        if (enable) {
            $("button.exp-control-on").removeClass('disabled');
            $("button.exp-control-off").addClass('disabled');
        } else {
            $("button.exp-control-on").addClass('disabled');
            $("button.exp-control-off").removeClass('disabled');
        }
    }

    function set_light_source(color_id) {
        $.post(
            document.location.href + "/light/" + LIGHT_COLOR_CODES[color_id]

        ).done(function() {
            update_bulb(color_id);
            $("button.bulb-control.disabled").removeClass("disabled");
            $("button#bulb-" + COLOR_NAMES[color_id]).addClass("disabled");

            return $.Deferred();

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
        if (sampler_timer || analyzer_timer) {
            stop_requested = true;

            img_ball.attr("src", "/img/ball-none.png");
            bar_graphs_container.addClass("invisible");
            clear_meters();
            enable_activation_buttons(true);

            set_light_source(OFF);
        }
    }

    function get_sample(repeat) {
        $.getJSON(
            document.location.href + "/sample"

        ).done(function(data) {
            update_meter(data.current);

            if (repeat && !stop_requested) {
                sampler_timer = setTimeout(
                    function() {
                        return get_sample(repeat);
                    },
                    1000
                );
            } else {
                sampler_timer = null;
                enable_activation_buttons(true);
                stop_requested = false;
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
        if (!analyzer_timer && !sampler_timer) {
            enable_activation_buttons(false);
            measure_display_simple.removeClass("invisible");
            measure_display_rgb.addClass("invisible");
            bar_graphs_container.addClass("invisible");

            get_sample(true);
        }
    }

    var analyzed_color = OFF
    var component_levels = [0, 0, 0];

    function max_index(elements) {
        var i = 1;
        var mi = 0;
        while (i < elements.length) {
            if (!(elements[i] < elements[mi])) {
                mi = i;
            }
            i += 1;
        }
        return mi;
    }

    function sample_and_analyze(repeat) {
        analyzed_color = (analyzed_color % 3) + 1;

        $.post(
            document.location.href + "/light/" + LIGHT_COLOR_CODES[analyzed_color]

        ).then(function() {
            update_bulb(analyzed_color);
            $("button.bulb-control.disabled").removeClass("disabled");
            $("button#bulb-" + COLOR_NAMES[analyzed_color]).addClass("disabled");

            return $.getJSON(document.location.href + "/sample");

        }).then(function(data) {
            update_rgb_meter(COLOR_NAMES[analyzed_color], data.current);
            component_levels[analyzed_color - 1] = data.current;

            if (analyzed_color === CYCLE_END) {
                return $.getJSON(
                    document.location.href + "/analyze",
                    {
                        "r" : component_levels[RED-1],
                        "g" : component_levels[GREEN-1],
                        "b" : component_levels[BLUE-1]
                    }
                );
            } else {
                return false;
            }

        }).done(function(data) {
            var end_of_cycle = false;
            var delay = 0;

            if (data.color) {
                img_ball.attr("src", "/img/ball-" + data.color + ".png");

                bar_graphs_container.removeClass("invisible");
                for (var i=0; i<3; i++) {
                    var pct = Math.round(data.decomp[i]) + "%";
                    bar_graphs[i].width(pct).text(pct);
                }
                end_of_cycle = true;
                set_light_source(OFF);
                // make a pause at the end of the cycle when repeat is active
                if (repeat)
                    delay = 1000;
            }

            if (stop_requested || (end_of_cycle && !repeat)) {
                stop_requested = false;
                analyzer_timer = null;
                enable_activation_buttons(true);

            } else {
                analyzer_timer = setTimeout(
                    function() {
                        return sample_and_analyze(repeat);
                    },
                    delay
                );
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

    function activate_analyzer(repeat) {
        if (!analyzer_timer && !sampler_timer) {
            $.getJSON(document.location.href + "/status")
            .done(function(result) {
                if (result.calibrated) {
                    enable_activation_buttons(false);
                    measure_display_simple.addClass("invisible");
                    measure_display_rgb.removeClass("invisible");

                    analyzed_color = OFF;
                    sample_and_analyze(repeat);
                } else {
                    jError("Le détecteur doit avoir été calibré avant.");
                }
            });
        }
    }

    for (var color_id=OFF; color_id<=BLUE; color_id++) {
        $("button#bulb-" + COLOR_NAMES[color_id]).click((function(clos_color){
            return function() {
                set_light_source(clos_color);
            };
        })(color_id));
    }

    $("button#sampling-on").click(function(){
        activate_sampler();
    });

    $("button#detection-on").click(function(){
        activate_analyzer(false);
    });

    $("#detection-single").click(function(e){
        activate_analyzer(false);
        e.preventDefault();
    });

    $("#detection-auto").click(function(e){
        activate_analyzer(true);
        e.preventDefault();
    });

    $("button#experiment-end").click(stop_sampling);

    $(window).unload(function(){
        stop_sampling();
        // ensure LED is off
        set_light_source(OFF);
    });

    update_meter(0);
    update_bulb(OFF);
});
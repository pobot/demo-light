$(document).ready(function() {
    'use strict';

    var OFF = 0;
    var RED = 1;
    var GREEN = 2;
    var BLUE = 3;
    var CYCLE_START = RED;
    var CYCLE_END = BLUE;

    var img_bulb = $("img#bulb");
    var img_ball = $("img#ball");
    var measure = $("#current");

    var measure_display_simple = $("#measure-display");
    var measure_display_rgb = $("#measure-rgb-display");

    var sampler_timer = null;
    var analyzer_timer = null;

    function update_meter(value) {
        measure.text(value.toFixed(3));
    }

    function update_rgb_meter(color, value) {
        $("div#" + color + " #current").text(value.toFixed(3));
    }

    function clear_meters() {
        $("div.measure-display span#current").text("0.000");
    }

    var color_ext = ["off", "red", "green", "blue"];

    function update_bulb(color) {
        img_bulb.attr("src", "/img/bulb-south-" + color_ext[color] + ".png");
    }

    function set_light_source(color) {
        $.ajax({
            url: document.location.href + "/light",
            data: {
                "color": color
            },
            method: "POST",
            success: function() {
                update_bulb(color);
                $("button.bulb-control.disabled").removeClass("disabled");
                $("button#bulb-" + color_ext[color]).addClass("disabled");
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
        if (sampler_timer || analyzer_timer) {
            if (sampler_timer) {
                clearTimeout(sampler_timer);
                sampler_timer = null;
            } else {
                clearTimeout(analyzer_timer);
                analyzer_timer = null;
            }
            img_ball.attr("src", "/img/ball-none.png");
            clear_meters();
            $("button.exp-control").toggleClass('disabled');

            set_light_source(OFF);
        }
    }

    function get_sample(repeat) {
        $.ajax({
            url: document.location.href + "/sample",
            dataType: "json",
            success: function(data) {
                update_meter(data.current);

                if (repeat) {
                    sampler_timer = setTimeout(
                        function() {
                            return get_sample(repeat);
                        },
                        1000
                    );
                }
           },
            error: function(jqXHR, textStatus, errorThrown) {
                jError(
                    "Erreur mesure : <br>" + errorThrown,
                    {
                        HideTimeEffect: 500
                    }
                );
            }
        });
    }

    function activate_sampler() {
        if (!analyzer_timer && !sampler_timer) {
            $("button.exp-control").toggleClass('disabled');
            measure_display_simple.removeClass("invisible");
            measure_display_rgb.addClass("invisible");

            get_sample(true);

        }
    }

    var detection_color = OFF
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

    function analyze(repeat) {
        detection_color = (detection_color % 3) + 1;

        $.ajax({
            url: document.location.href + "/light",
            data: {
                "color": detection_color
            },
            method: "POST",
            success: function() {
                update_bulb(detection_color);
                $("button.bulb-control.disabled").removeClass("disabled");
                $("button#bulb-" + color_ext[detection_color]).addClass("disabled");

                $.ajax({
                    url: document.location.href + "/sample",
                    dataType: "json",
                    success: function(data) {
                        update_rgb_meter(color_ext[detection_color], data.current);
                        component_levels[detection_color - 1] = data.current;

                        if (detection_color === CYCLE_END) {
                            var color = max_index(component_levels) + 1;
                            img_ball.attr("src", "/img/ball-" + color_ext[color] + ".png");
                        }

                        if (repeat) {
                            analyzer_timer = setTimeout(
                                function() {
                                    return analyze(repeat);
                                },
                                1000
                            );
                        }
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        jError(
                            "Erreur mesure : <br>" + errorThrown,
                            {
                                HideTimeEffect: 500
                            }
                        );
                    }
                });

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

    function activate_analyzer() {
        if (!analyzer_timer && !sampler_timer) {
            $("button.exp-control").toggleClass('disabled');
            measure_display_simple.addClass("invisible");
            measure_display_rgb.removeClass("invisible");

            detection_color = OFF;
            analyze(true);

        }
    }

    for (var color=OFF; color<=BLUE; color++) {
        $("button#bulb-" + color_ext[color]).click((function(clos_color){
            return function() {
                set_light_source(clos_color);
            };
        })(color));
    }

    $("button#sampling-on").click(function(){
        activate_sampler();
    });

    $("button#detection-on").click(function(){
        activate_analyzer();
    });

    $("button#experiment-end").click(stop_sampling);

    $(window).unload(stop_sampling);

    update_meter(0);
    update_bulb(OFF);
});
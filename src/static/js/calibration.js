$(document).ready(function() {
    'use strict';

    var current_free = 0, current_occupied = 0;
    var current_white = 0, current_black = 0;
    var color_done_w = false, color_done_b = false;
    var current_r, current_g, current_b;

    var calibration_data = {
        barrier: [0, 0],
        bw_detector: [0, 0],
        color_detector: {
            b: [0, 0, 0],
            w: [0, 0, 0]
        }
    };

    function set_calibrated(elt, done) {
        if (done) {
            elt.text("calibrage OK")
                .removeClass("text-danger")
                .addClass("text-success")
            ;
        } else {
            elt.text("calibrage non fait")
                .removeClass("text-success")
                .addClass("text-danger")
            ;
        }
    }

    set_calibrated($("div.calibration-status"), false);

    $.getJSON(document.location.href + "/data").done(
        function(data) {
            calibration_data = data;

            // inject calibration data in the page
            var step, done;

            for (step=done=0; step<2; step++) {
                var value = calibration_data.barrier[step];
                if (value != 0) {
                    var parent_id = "div#barrier_" + step;
                    $(parent_id + " span#value").text(value.toFixed(3));
                    $(parent_id + " span#level").removeClass("invisible");
                    $(parent_id + " span#status-led").addClass("done");
                    if (step == 0) {
                        current_free = value;
                    } else {
                        current_occupied = value;
                    }
                    done++;
                }
            }
            if (done == step) {
                set_calibrated($("div#barrier div.calibration-status"), true);
            }

            for (step=done=0; step<2; step++) {
                var value = calibration_data.bw_detector[step];
                if (value != 0) {
                    var parent_id = "div#bw_" + ['b', 'w'][step];
                    $(parent_id + " span#value").text(value.toFixed(3));
                    $(parent_id + " span#level").removeClass("invisible");
                    $(parent_id + " span#status-led").addClass("done");
                    if (step == 0) {
                        current_black = value;
                    } else {
                        current_white = value;
                    }
                    done++;
                }
            }
            if (done == step) {
                set_calibrated($("div#bw_detector div.calibration-status"), true);
            }

            var done_color_steps = 0;

            for (step=done=0; step<3; step++) {
                var value = calibration_data.color_detector.w[step];
                if (value != 0) {
                    var parent_id = "div#white_balance li#step-" + (step + 1);
                    $(parent_id + " span#value").text(value.toFixed(3));
                    $(parent_id + " span#level").removeClass("invisible");
                    $(parent_id + " span#status-led").addClass("done");
                    done++;
                }
            }
            if (done == step) {
                color_done_w = true;
                done_color_steps++;
            }

            for (step=done=0; step<3; step++) {
                var value = calibration_data.color_detector.b[step];
                if (value != 0) {
                    var parent_id = "div#black_levels li#step-" + (step + 1);
                    $(parent_id + " span#value").text(value.toFixed(3));
                    $(parent_id + " span#level").removeClass("invisible");
                    $(parent_id + " span#status-led").addClass("done");
                    done++;
                }
            }
            if (done == step) {
                color_done_b = true;
                done_color_steps++;
            }

            if (done_color_steps == 2) {
                set_calibrated($("div#color div.calibration-status"), true);
            }
        }
    );

    function running(state) {
        if (state) {
            $("div#running").show() ;
        } else {
            $("div#running").hide() ;
        }
    }

    function calibration_started(msg) {
        $("button#go").addClass('disabled');
        running(true);
    }

    function calibration_ended() {
        running(false);
        $("button#go").removeClass('disabled');
    }

    function notify(msg) {
        jNotify(msg, {ShowOverlay: true});
    }

    function success(msg) {
        jSuccess(msg, {ShowOverlay: false});
    }

    function error(msg) {
        jError(msg, {ShowOverlay: false});
    }

    function calibrate_barrier(occupied) {
        var div = "div#barrier_" + occupied + " ";

        calibration_started("Calibrage barrière lumineuse démarré.");

        set_calibrated($("div#barrier div.calibration-status"), false);
        $(div + "li span.status").removeClass("done");
        $(div + "span#level").addClass("invisible");

        $.getJSON(document.location.href + "/barrier/sample").then(
            function(result) {
                var current = result.current;
                var div_step = div + "li#step-1 ";

                $(div_step + "span#value").text(current.toFixed(3));
                $(div_step + "span#level").removeClass("invisible");
                $(div_step + "span.status").addClass("done");

                if (occupied === "1") {
                    current_occupied = current;
                } else {
                    current_free = current;
                }

                if (current_free !== 0 && current_occupied !== 0) {
                    return $.post(
                        document.location.href + "/barrier/store",
                        {"free": current_free, "occupied": current_occupied}
                    );
                }
            }
        ).done(
            function(result) {
                if (current_free !== 0 && current_occupied !== 0) {
                    set_calibrated($("div#barrier div.calibration-status"), true);
                }
                success("Calibrage terminé.");
            }
        ).fail(
            function(jqXHR, textStatus, errorThrown) {
                error("Erreur traitement : <br>" + errorThrown);
            }
        ).always(
            calibration_ended
        );
    }

    function calibrate_bw_detector(color) {
        var div = "div#bw_" + color + " ";

        calibration_started("Calibrage détecteur noir/blanc démarré.");

        set_calibrated($("div#bw_detector div.calibration-status"), false);
        $(div +"li span.status").removeClass("done");
        $(div + "li#step-1 span#level").addClass("invisible");

        $.getJSON(document.location.href + "/bw_detector/sample").then(
            function(result){
                var current = result.current;
                var div_step = div + "li#step-1 ";

                $(div_step + "span#value").text(current.toFixed(3));
                $(div_step + "span#level").removeClass("invisible");
                $(div_step + "span.status").addClass("done");

                if (color === 'w') {
                    current_white = current;
                } else {
                    current_black = current;
                }

                if (current_black !== 0 && current_white !== 0) {
                    return $.post(
                        document.location.href + "/bw_detector/store",
                        {"w" : current_white, "b" : current_black}
                    );
                }
            }
        ).done(
            function() {
                if (current_black !== 0 && current_white !== 0) {
                    set_calibrated($("div#bw_detector div.calibration-status"), true);
                }
                success("Calibrage terminé.");
            }
        ).fail(
            function(jqXHR, textStatus, errorThrown) {
                error("Erreur traitement : <br>" + errorThrown);
            }
        ).always(
            calibration_ended
        );
    }

    function calibrate_color_detector(w_or_b) {
        var div = "div#" + (w_or_b == 'w' ? "white_balance" : "black_levels") + " ";

        calibration_started("Balance des blancs démarrée.");

        set_calibrated($("div#color div.calibration-status"), false);
        $(div + "li span.status").removeClass("done");
        $(div + "span#level").addClass("invisible");

        $.getJSON(
            document.location.href + "/color_detector/sample",
            {"color" : "r"}

        ).then(function(result) {
            current_r = result.current;
            var div_step = div + "li#step-1 ";

            $(div_step + "span#value").text(result.current.toFixed(3));
            $(div_step + "span#level").removeClass("invisible");
            $(div_step + "span.status").addClass("done");

            return $.getJSON(
                document.location.href + "/color_detector/sample",
                {"color" : "g"}
            );

        }).then(function(result) {
            var div_step = div + "li#step-2 ";

            current_g = result.current;
            $(div_step + "span#value").text(result.current.toFixed(3));
            $(div_step + "span#level").removeClass("invisible");
            $(div_step + "span.status").addClass("done");

            return $.getJSON(
                document.location.href + "/color_detector/sample",
                {"color" : "b"}
            );

        }).then(function(result) {
            var div_step = div + "li#step-3 ";

            current_b = result.current;
            $(div_step + "span#value").text(result.current.toFixed(3));
            $(div_step + "span#level").removeClass("invisible");
            $(div_step + "span.status").addClass("done");

            return $.post(
                document.location.href + "/color_detector/store/" + w_or_b,
                {"r" : current_r, "g" : current_g, "b" : current_b}
            );

        }).done(function() {
            if (w_or_b === 'w') {
                color_done_w = true;
            } else {
                color_done_b = true;
            }
            if (color_done_w && color_done_b) {
                set_calibrated($("div#color div.calibration-status"), true);
            }
            success("Calibrage terminé.");

        }).fail(function(jqXHR, textStatus, errorThrown) {
            error("Erreur traitement : <br>" + errorThrown);

        }).always(
            calibration_ended
        );
    }

    $("div.panel-heading button").click(function(){
        $("div.panel-body").hide();
        $("div.panel-body", $(this).parents(".panel")).show();
    });

    $("div.panel-body").hide();

    $("div#barrier_0 button#go").click(function(){
        calibrate_barrier('0');
    });

    $("div#barrier_1 button#go").click(function(){
        calibrate_barrier('1');
    });

    $("div#bw_w button#go").click(function(){
        calibrate_bw_detector('w');
    });

    $("div#bw_b button#go").click(function(){
        calibrate_bw_detector('b');
    });

    $("div#white_balance button#go").click(function(){
        calibrate_color_detector('w');
    });

    $("div#black_levels button#go").click(function(){
        calibrate_color_detector('b');
    });

});
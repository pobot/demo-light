$(document).ready(function() {
    'use strict';

    function running(state) {
        if (state) {
            $("div#running").removeClass("invisible");
        } else {
            $("div#running").addClass("invisible");
        }
    }

    function calibration_started(msg) {
        $("button#go").addClass('disabled');
        jNotify(msg, {ShowOverlay: false});
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

    function calibrate_barrier() {
        var current_ambient, current_lightened;
        var div = "div#barrier ";

        calibration_started("Calibrage barrière lumineuse démarré.");

        $(div + "li span.status").removeClass("done");
        $(div + "span#level").addClass("invisible");

        $.getJSON(document.location.href + "/barrier/step/0").then(
            function(result){
                current_ambient = result.current;
                var div_step = div + "li#step-1 ";

                $(div_step + "span#value").text(current_ambient.toFixed(3));
                $(div_step + "span#level").removeClass("invisible");
                $(div_step + "span.status").addClass("done");

                return $.getJSON(document.location.href + "/barrier/step/1");
            }
        ).then(
            function(result) {
                var div_step = div + "li#step-2 ";

                current_lightened = result.current;
                $(div_step + "span#value").text(current_lightened.toFixed(3));
                $(div_step + "span#level").removeClass("invisible");
                $(div_step + "span.status").addClass("done");

                return $.post(
                    document.location.href + "/barrier/store",
                    {"ambient" : current_ambient, "lightened" : current_lightened}
                )
            }
        ).done(
            function(result) {
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

    var current_white = 0, current_black = 0;

    function calibrate_bw_detector(color) {
        var div = "div#bw_" + color + " ";

        calibration_started("Calibrage détecteur noir/blanc démarré.");

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
        var current_r, current_g, current_b;
        var div = "div#" + (w_or_b == 'w' ? "white_balance" : "black_levels") + " ";

        calibration_started("Balance des blancs démarrée.");

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
            success("Calibrage terminé.");

        }).fail(function(jqXHR, textStatus, errorThrown) {
            error("Erreur traitement : <br>" + errorThrown);

        }).always(
            calibration_ended
        );
    }

    $("div#barrier button#go").click(function(){
        calibrate_barrier();
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
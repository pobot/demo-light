$(document).ready(function() {
    'use strict';

    function notify(msg) {
        jNotify(
            msg,
            {
                ShowTimeEffect: 200,
                TimeShown: 1000,
                HideTimeEffect: 200,
                ShowOverlay: false
            }
        );
    }

    function success(msg) {
        jSuccess(
            msg,
            {
                TimeShown: 1000,
                ShowOverlay: false
            }
        );
    }

    function error(msg) {
        jError(
            msg,
            {
                TimeShown: 1500,
                ShowOverlay: false
            }
        );
    }

    function calibrate_barrier() {
        var current_ambient, current_lightened;

        notify("Calibrage barrière lumineuse démarré.");
        $("div#barrier li span.status").removeClass("done");

        $.ajax({
            url: document.location.href + "/barrier/0",
            dataType: "json",
            success: function(result) {
                current_ambient = result.current;
                $("div#barrier li#step-1 span#value").text(current_ambient.toFixed(3));
                $("div#barrier li#step-1 span#level").removeClass("invisible");
                $("div#barrier li#step-1 span.status").addClass("done");

                $.ajax({
                    url: document.location.href + "/barrier/1",
                    dataType: "json",
                    success: function(result) {
                        current_lightened = result.current;
                        $("div#barrier li#step-2 span#value").text(current_lightened.toFixed(3));
                        $("div#barrier li#step-2 span#level").removeClass("invisible");
                        $("div#barrier li#step-2 span.status").addClass("done");

                        $.ajax({
                            url: document.location.href + "/barrier",
                            method: "POST",
                            data: {"ambient" : current_ambient, "lightened" : current_lightened},
                            success: function(result) {
                                success("Calibrage terminé.");
                            },
                            error: function(jqXHR, textStatus, errorThrown) {
                                error("Erreur traitement : <br>" + errorThrown);
                            }
                        });
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        error("Erreur traitement : <br>" + errorThrown);
                    }
                });

            },
            error: function(jqXHR, textStatus, errorThrown) {
                error("Erreur traitement : <br>" + errorThrown);
            }
        });
    }

    var current_white = 0, current_black = 0;

    function calibrate_bw_detector(color) {
        var div = "div#bw_" + color + " ";

        notify("Calibrage détecteur noir/blanc démarré.");
        $(div +"li span.status").removeClass("done");

        $.ajax({
            url: document.location.href + "/bw_detector/sample",
            dataType: "json",
            success: function(result) {
                var current = result.current;
                $(div + "li#step-1 span#value").text(current.toFixed(3));
                $(div + "li#step-1 span#level").removeClass("invisible");
                $(div + "li#step-1 span.status").addClass("done");

                if (color === 'w') {
                    current_white = current;
                } else {
                    current_black = current;
                }

                if (current_black !== 0 && current_white !== 0) {
                    $.ajax({
                        url: document.location.href + "/bw_detector",
                        method: "POST",
                        data: {"w" : current_white, "b" : current_black},
                        success: function(result) {
                            success("Calibrage terminé.");
                        },
                        error: function(jqXHR, textStatus, errorThrown) {
                            error("Erreur traitement : <br>" + errorThrown);
                        }
                    });
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                error("Erreur traitement : <br>" + errorThrown);
            }
        });
    }

    function calibrate_white_balance() {
        notify("Balance des blancs démarrée.");
    }

    function calibrate_black_levels() {
        notify("Calibrage des niveaux de noir démarré.");
    }

    $("div#barrier button#go").click(function(){
        $(this).toggleClass('disabled');
        calibrate_barrier();
        $(this).toggleClass('disabled');
    });

    $("div#bw_w button#go").click(function(){
        $(this).toggleClass('disabled');
        calibrate_bw_detector('w');
        $(this).toggleClass('disabled');
    });

    $("div#bw_b button#go").click(function(){
        $(this).toggleClass('disabled');
        calibrate_bw_detector('b');
        $(this).toggleClass('disabled');
    });

    $("div#white_balance button#go").click(function(){
        $(this).toggleClass('disabled');
        calibrate_white_balance();
        $(this).toggleClass('disabled');
    });

    $("div#black_levels button#go").click(function(){
        $(this).toggleClass('disabled');
        calibrate_black_levels();
        $(this).toggleClass('disabled');
    });

});
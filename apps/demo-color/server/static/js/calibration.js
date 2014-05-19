$(document).ready(function() {
    'use strict';

    function calibrate_barrier() {
        jNotify("Calibrage barrière lumineuse démarré.");
        $("div#barrier li span.status").removeClass("done");

        $.ajax({
            url: document.location.href + "/barrier/0",
            dataType: "json",
            async: false,
            success: function(result) {
                $("div#barrier li#step-1 span#value").text(result.voltage.toFixed(3));
                $("div#barrier li#step-1 span#level").removeClass("invisible");
                $("div#barrier li#step-1 span.status").addClass("done");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                jError(
                    "Erreur traitement : <br>" + errorThrown,
                    {
                        HideTimeEffect: 500
                    }
                );
            }
        });

        $.ajax({
            url: document.location.href + "/barrier/1",
            dataType: "json",
            async: false,
            success: function(result) {
                $("div#barrier li#step-2 span#value").text(result.voltage.toFixed(3));
                $("div#barrier li#step-2 span#level").removeClass("invisible");
                $("div#barrier li#step-2 span.status").addClass("done");

                jSuccess("Calibrage barrière lumineuse terminé.");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                jError(
                    "Erreur traitement : <br>" + errorThrown,
                    {
                        HideTimeEffect: 500
                    }
                );
            }
        });
    }

    function calibrate_bw_detector() {
        jNotify("Calibrage détecteur blanc/noir démarré.");
        $("div#bw_detector li span.status").removeClass("done");

        $.ajax({
            url: document.location.href + "/bw_detector/0",
            dataType: "json",
            async: false,
            success: function(result) {
                $("div#bw_detector li#step-1 span#value").text(result.voltage.toFixed(3));
                $("div#bw_detector li#step-1 span#level").removeClass("invisible");
                $("div#bw_detector li#step-1 span.status").addClass("done");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                jError(
                    "Erreur traitement : <br>" + errorThrown,
                    {
                        HideTimeEffect: 500
                    }
                );
            }
        });

        $.ajax({
            url: document.location.href + "/bw_detector/1",
            dataType: "json",
            async: false,
            success: function(result) {
                $("div#bw_detector li#step-2 span#value").text(result.voltage.toFixed(3));
                $("div#bw_detector li#step-2 span#level").removeClass("invisible");
                $("div#bw_detector li#step-2 span.status").addClass("done");

                jSuccess("Calibrage détecteur blanc/noir terminé.");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                jError(
                    "Erreur traitement : <br>" + errorThrown,
                    {
                        HideTimeEffect: 500
                    }
                );
            }
        });
    }

    function calibrate_white_balance() {
        jNotify("Balance des blancs démarrée.");
    }

    function calibrate_black_levels() {
        jNotify("Calibrage des niveaux de noir démarré.");
    }

    $("div#barrier button#go").click(function(){
        $(this).toggleClass('disabled');
        calibrate_barrier();
        $(this).toggleClass('disabled');
    });

    $("div#bw_detector button#go").click(function(){
        $(this).toggleClass('disabled');
        calibrate_bw_detector();
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
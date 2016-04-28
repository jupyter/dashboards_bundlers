/**
 * Copyright (c) Jupyter Development Team.
 * Distributed under the terms of the Modified BSD License.
 */
define(['jquery', 'Thebe', 'urth-common/error-log'], function($, Thebe, ErrorLog) {
    'use strict';

    var $container, thebe;

    function getQueryParam(name) {
        var vars = window.location.search.substring(1).split('&');
        for (var i = 0; i < vars.length; i++) {
            var pair = vars[i].split('=');
            if (pair[0] === name) {
                return decodeURIComponent(pair[1]);
            }
        }
        return null;
    }

    function initThebe(args) {
        thebe = new Thebe.Thebe({
            url: args.url,
            debug: false,
            append_kernel_controls_to: 'body',
            next_cell_shortcut: false,
            inject_css: false, // don't pull in mathjax, jqueryui, etc. for now
            tmpnb_mode: Urth.tmpnb_mode || false,
            kernel_name: Urth.kernel_name,
            load_css: false
        });

        // Shims for libs that think they are in the notebook environment
        window.IPython.notebook = thebe.notebook;
        window.Jupyter = window.IPython;
        thebe.notebook.base_url = 'static/';

        // show a busy indicator when communicating with kernel
        var debounced;
        thebe.events.on('kernel_busy.Kernel kernel_idle.Kernel', function(event) {
            clearTimeout(debounced);
            debounced = setTimeout(function() {
                var isBusy = event.type === 'kernel_busy';
                $('.busy-indicator')
                    .toggleClass('show', isBusy)
                    // Prevent progress animation when hidden by removing 'active' class.
                    .find('.progress-bar')
                        .toggleClass('active', isBusy);
            }, 500);
        });

        // hook the error handler to kernel / session events
        thebe.events.on('kernel_created.Kernel kernel_created.Session', function(e) {
            ErrorLog.enable(window.IPython);
        });

        // finally, let's start the kernel (rather than waiting for it to be lazily loaded)
        var kernel_ready = new $.Deferred();
        if(Urth.tmpnb_mode) {
            thebe.call_spawn(kernel_ready.resolve);
        } else {
            thebe.start_kernel(kernel_ready.resolve);
        }

        return kernel_ready;
    }

    function initGrid() {
        var deferred = $.Deferred();
        require(['urth-common/gridstack-custom'], function(Gridstack) {
            $container.addClass('grid-stack');

            // enable gridstack
            var gridstack = $container.gridstack({
                vertical_margin: Urth.cellMargin,
                cell_height: Urth.defaultCellHeight,
                width: Urth.maxColumns,
                static_grid: true
            }).data('gridstack');

            var halfMargin = Urth.cellMargin / 2;
            var styleRules = [
                {
                    selector: '#dashboard-container .grid-stack-item.rendered_html',
                    rules: 'padding: ' + halfMargin + 'px ' + (halfMargin + 6) + 'px;',
                }
            ];
            gridstack.generateStylesheet(styleRules);

            deferred.resolve();
        });
        return deferred;
    }

    function showRow(row, col) {
        $('body').addClass('show-row-only');
        var $cells = $container.find('.grid-stack-item');

        var rowAttr = '[data-gs-y="' + row + '"]';
        $cells.filter(':not(' + rowAttr + ')').hide();

        if (col) {
            // show a single cell
            $('body').addClass('single-cell');
            var colAttr = '[data-gs-x="' + col + '"]';
            $cells.filter(':not(' + colAttr + ')').hide();
        } else {
            // show full row
            $cells.filter(rowAttr).css('flex', function() {
                var $cell = $(this);
                var sizex = $cell.attr('data-gs-width');
                return sizex + ' 0 ' + sizex + 'px';
            });
        }
    }

    function _showDashboard() {
        $('#outer-dashboard').css('visibility', '');
    }

    return {
        init: function() {
            $container = $('#dashboard-container');

            // initialize thebe
            var thebe_ready = initThebe({
                url: Urth.thebe_url
            });

            // initialize the layout
            var layout_ready = true, showBackground = true;
            if (Urth.layout === 'grid') {
                var row = getQueryParam('row');
                if (!row) {
                    layout_ready = initGrid();
                } else {
                    showBackground = false;
                    showRow(row, getQueryParam('col')); // show only given row/column
                }
            }
            $('body').toggleClass('dashboard-view', showBackground);

            // we're fully initialized when both grid and thebe are initialized
            return $.when(layout_ready, thebe_ready).then(_showDashboard);
        },

        executeAll: function() {
            thebe.run_cell(0, thebe.cells.length);
        }
    };
});

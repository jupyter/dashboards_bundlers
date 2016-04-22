{#-
 Copyright (c) Jupyter Development Team.
 Distributed under the terms of the Modified BSD License.
-#}
<!DOCTYPE HTML>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ nb.name }}</title>
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <script>
        var IPython = {};
        var Urth = window.Urth = window.Urth || {};
{% block thebe_config %}
        Urth.thebe_url = (function thebe_url() {
            var origin = window.location.origin;
            var pathname = window.location.pathname;
            var start = pathname.search('/files');
            var path = pathname.slice(0, start);
            return origin + path;
        })();
        Urth.tmpnb_mode = false;
{% endblock %}
        Urth.kernel_name = '{%- if (nb.metadata is defined) and (nb.metadata.kernelspec is defined) and (nb.metadata.kernelspec.name is defined) %}
            {{- nb.metadata.kernelspec.name -}}
        {%- endif -%}' || 'python3';
        {% if (nb.metadata is defined) and (nb.metadata.urth is defined) and (nb.metadata.urth.dashboard is defined) -%}
            {%- set dashboardLayout = nb.metadata.urth.dashboard.layout or "grid" -%}
            {%- set maxColumns = nb.metadata.urth.dashboard.maxColumns or 12 -%}
            {%- set cellMargin = nb.metadata.urth.dashboard.cellMargin or 10-%}
            {%- set defaultCellHeight = nb.metadata.urth.dashboard.defaultCellHeight or 20 -%}
            {%- set useFallbackValues = false -%}
        {%- else -%}
            {%- set dashboardLayout = "grid" -%}
            {%- set maxColumns = 12 -%}
            {%- set cellMargin = 10 -%}
            {%- set cellRowSpan = 4 -%}
            {%- set defaultCellHeight = 20 -%}
            {%- set useFallbackValues = true -%}
        {%- endif -%}
        Urth.layout = "{{dashboardLayout}}";
        Urth.maxColumns = {{maxColumns}};
        Urth.cellMargin = {{cellMargin}};
        Urth.defaultCellHeight = {{defaultCellHeight}};
    </script>
    <script data-main="./static/main.js" src="./static/bower_components/requirejs/require.js"></script>

    <link rel="stylesheet" type="text/css" href="./static/bower_components/jquery-ui/themes/smoothness/jquery-ui.min.css">
    {% if (dashboardLayout == "grid") -%}
    <link rel="stylesheet" type="text/css" href="./static/bower_components/gridstack/dist/gridstack.min.css">
    <link rel="stylesheet" type="text/css" href="./static/dashboard-common/gridstack-overrides.css">
    {% endif -%}
    <link rel="stylesheet" type="text/css" href="./static/ipython/style.min.css">
    <link rel="stylesheet" type="text/css" href="./static/dashboard-common/dashboard-common.css">
    <link rel="stylesheet" type="text/css" href="./static/urth/dashboard.css">
</head>

<body class="urth-dashboard">

<noscript>
<div id='noscript'>
    This page requires JavaScript.<br>
    Please enable it to proceed.
</div>
</noscript>

<div id="outer-dashboard" class="container" style="visibility: hidden;">
    <div id="dashboard-container" class="container" data-dashboard-layout="{{dashboardLayout}}">
        {%- for cell in nb.cells -%}
            {%- if (cell.metadata is defined) and (cell.metadata.urth is defined) and (cell.metadata.urth.dashboard is defined) -%}
                {%- set hidden = cell.metadata.urth.dashboard.hidden -%}
                {%- set layout = cell.metadata.urth.dashboard.layout -%}
            {%- endif -%}
            {%- if (dashboardLayout == "grid") and (layout == none) -%}
                {%- if (useFallbackValues) -%}
                    {%- set hidden = false -%}
                    {%- set layout = { 'width': maxColumns, 'height': cellRowSpan, 'row': 0, 'col': 0 } -%}
                {%- else -%}
                    {%- set hidden = none -%}
                    {%- set layout = none -%}
                {%- endif -%}
            {%- endif -%}
            {# Thebe doesn't wrap HTML-converted cells with same structure as seen in Notebook,
               resulting in different styling. Adding necessary classes to match styles. #}
            {%- set textClass = "rendered_html" if (cell.cell_type is defined) and (cell.cell_type == "markdown") else "" -%}
            <div {% if (dashboardLayout == "report") -%}
                    class="report-cell {{textClass}} {%- if (hidden) -%} dashboard-hidden{%- endif -%}"
                {%- else -%}
                    {%- if (useFallbackValues) -%}
                        data-gs-auto-position='true'
                    {%- endif -%}
                    {%- if (hidden != none) and (not hidden) and (layout != none) -%}
                        data-gs-x={{layout.col}} data-gs-y={{layout.row}}
                        data-gs-width={{layout.width}} data-gs-height={{layout.height}}
                        class="grid-stack-item {{textClass}}"
                    {%- endif %}
                {%- endif -%}>
                {%- if cell.cell_type in ['markdown'] -%}
                    {{cell.source | markdown2html | strip_files_prefix }}
                {%- elif cell.cell_type == 'code' -%}
<pre data-executable="true">
{{cell.source|e}}
</pre>
                {%- endif -%}
            </div>
        {%- endfor -%}
    </div>
</div>

<div class="busy-indicator progress">
    <div class="progress-bar progress-bar-striped" role="progressbar" aria-valuenow="100"
        aria-valuemin="0" aria-valuemax="100" style="width: 100%;"></div>
</div>

</body>
</html>

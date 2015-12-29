{#-
 Copyright (c) Jupyter Development Team.
 Distributed under the terms of the Modified BSD License.
-#}
{% extends "index.html.tpl" %}
{% block thebe_config %}
        Urth.thebe_url = '<?php echo $_ENV["KERNEL_SERVICE_URL"] ?>';
        Urth.tmpnb_mode = ('<?php echo $_ENV["TMPNB_MODE"] ?>' === 'true');
{% endblock %}
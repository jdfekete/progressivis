import ipywidgets as widgets
from traitlets import Unicode, Any

# See js/lib/widgets.js for the frontend counterpart to this file.

@widgets.register
class Scatterplot(widgets.DOMWidget):
    """Progressivis Scatterplot widget."""

    # Name of the widget view class in front-end
    _view_name = Unicode('ScatterplotView').tag(sync=True)

    # Name of the widget model class in front-end
    _model_name = Unicode('ScatterplotModel').tag(sync=True)

    # Name of the front-end module containing widget view
    _view_module = Unicode('progressivis-nb-widgets').tag(sync=True)

    # Name of the front-end module containing widget model
    _model_module = Unicode('progressivis-nb-widgets').tag(sync=True)

    # Version of the front-end module containing widget view
    _view_module_version = Unicode('^0.1.0').tag(sync=True)
    # Version of the front-end module containing widget model
    _model_module_version = Unicode('^0.1.0').tag(sync=True)

    # Widget specific property.
    # Widget properties are defined as traitlets. Any property tagged with `sync=True`
    # is automatically synced to the frontend *any* time it changes in Python.
    # It is synced back to Python from the frontend *any* time the model is touched.
    data = Unicode('{}').tag(sync=True)
    value =  Any('{}').tag(sync=True)

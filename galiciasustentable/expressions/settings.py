from qgis.core import QgsSettings

@qgsfunction(args='auto', group='EPyRIS', usesgeometry=False)
def settings_value(key, fallback_value, feature, parent):
    settings = QgsSettings()
    return settings.value(key=key, defaultValue=fallback_value)
    
@qgsfunction(args='auto', group='EPyRIS', usesgeometry=False)
def settings_set_value(key, value, feature, parent):
    settings = QgsSettings()
    return settings.setValue(key=key, value=value)

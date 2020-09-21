from processing.core.ProcessingConfig import ProcessingConfig

@qgsfunction(args='auto', group='GaliciaSustentable', usesgeometry=False)
def processing_config_value(key, feature, parent):
    return ProcessingConfig.getSetting(key)
    
@qgsfunction(args='auto', group='GaliciaSustentable', usesgeometry=False)
def processing_config_set_value(key, value, feature, parent):
    return ProcessingConfig.setSettingValue(key, value)

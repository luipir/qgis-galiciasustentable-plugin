import os

@qgsfunction(args='auto', group='EPyRIS', usesgeometry=False)
def path_utils_join(paths, feature, parent):
    return os.path.join(*paths)

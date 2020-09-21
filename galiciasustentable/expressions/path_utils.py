import os

@qgsfunction(args='auto', group='GaliciaSustentable', usesgeometry=False)
def path_utils_join(paths, feature, parent):
    return os.path.join(*paths)

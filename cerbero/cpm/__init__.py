
    
class PkgFileProcessor(object):    
    
    def __init__(self,root_dir):
        self.rootd = root_dir

    def process(self, arcname, content):
        raise Exception("Not Implemented")

class PkgFileSkipper(PkgFileProcessor):

    def __init__(self,root_dir):
        PkgFileProcessor.__init__(self, root_dir)

    def process(self, arcname, content):
        return None



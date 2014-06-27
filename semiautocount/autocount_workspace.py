
import os

from . import util, images

from nesoni import workspace



class Autocount_workspace(workspace.Workspace):
    def __init__(self, working_dir, must_exist):
        workspace.Workspace.__init__(self, working_dir, must_exist)
        
        if must_exist:        
            self.index = util.load(self/'index.pgz')
    
    def get_config(self):
        from . import configure
        filename = self/'config.pgz'
        if not os.path.exists(filename):
            return configure.Config()
        return util.load(filename)
    
    def set_config(self, config):
        util.save(self/'config.pgz', config)
    
    def get_image(self, i):
        return images.load(self/(self.index[i]+'.png'))

    def get_segmentation(self, i):
        return util.load(self/(self.index[i]+'-segmentation.pgz'))

    
    def get_labels(self, i):
        return util.load(self/(self.index[i]+'-labels.pgz'))

    def set_labels(self, i, value):
        return util.save(self/(self.index[i]+'-labels.pgz'), value)


    def has_classification(self, i):
        return os.path.exists(self/(self.index[i]+'-classification.pgz'))

    def get_classification(self, i):
        return util.load(self/(self.index[i]+'-classification.pgz'))

    def set_classification(self, i, value):
        return util.save(self/(self.index[i]+'-classification.pgz'), value)

    
    def get_measure(self, i):
        from . import measure
    
        filename = self/(self.index[i]+'-measure.pgz')
        ok = os.path.exists(filename)
        if ok:
            result = util.load(filename)
            ok = (result.version == measure.VERSION)        
        if not ok:
            result = measure.measure(self, i)
            util.save(filename, result)
        return result

import os

from . import util, images

from nesoni import workspace



class Autocount_workspace(workspace.Workspace):
    def __init__(self, working_dir, must_exist):
        workspace.Workspace.__init__(self, working_dir, must_exist)
        
        workspace.Workspace(self/'images', must_exist=False)
        workspace.Workspace(self/'config', must_exist=False)
        
        if must_exist:        
            self.index = util.load(self/('config','index.pgz'))
    
    def get_config(self):
        from . import configure
        filename = self/('config','config.pgz')
        if not os.path.exists(filename):
            return configure.Config()
        return util.load(filename)
    
    def set_config(self, config):
        util.save(self/('config','config.pgz'), config)
    
    @util.cached(1)
    def get_image(self, i):
        return images.load(self/('images',self.index[i]+'.png'))

    def get_segmentation(self, i):
        return util.load(self/('images',self.index[i]+'-segmentation.pgz'))

    
    def get_labels(self, i):
        return util.load(self/('images',self.index[i]+'-labels.pgz'))

    def set_labels(self, i, value):
        return util.save(self/('images',self.index[i]+'-labels.pgz'), value)


    def has_classification(self, i):
        return os.path.exists(self/('images',self.index[i]+'-classification.pgz'))

    def get_classification(self, i):
        return util.load(self/('images',self.index[i]+'-classification.pgz'))

    def set_classification(self, i, value):
        return util.save(self/('images',self.index[i]+'-classification.pgz'), value)

    def get_calls(self, i, label_override):
        if not self.has_classification(i):
            calls = [ None ] * len(labels)
        else:
            calls = self.get_classification(i).call[:]
        
        if label_override:
            labels = self.get_labels(i)
            for j in xrange(len(calls)):
                if labels[j] is not None:
                    calls[j] = labels[j]

        return calls

    
    def get_measure(self, i):
        from . import measure
    
        filename = self/('images',self.index[i]+'-measure.pgz')
        ok = os.path.exists(filename)
        if ok:
            result = util.load(filename)
            ok = (result.version == measure.VERSION)        
        if not ok:
            result = measure.measure(self, i)
            util.save(filename, result)
        return result




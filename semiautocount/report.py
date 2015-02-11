

from nesoni import config, workspace

from . import util, autocount_workspace


@config.help(
    'Generate output files.',
    )
class Report(config.Action_with_working_dir):
    _workspace_class = autocount_workspace.Autocount_workspace

    def run(self):
        work = self.get_workspace()
        config = work.get_config()
        
        work_coordinates = workspace.Workspace(work/'coordinates', must_exist=False)

        counts = [ [0]*len(config.labels) for i in xrange(len(work.index)) ]
        manual_counts = [ [0]*len(config.labels) for i in xrange(len(work.index)) ]
        
        for i, name in enumerate(work.index):
            print i, name
            
            seg = work.get_segmentation(i)
            calls = work.get_calls(i, True, True)
            manual_calls = work.get_calls(i, False, True)
            
            with open(work_coordinates/(name+'.csv'),'wb') as f:
                print >> f, 'x,y,call,manual_label'
                for j in xrange(len(seg.bounds)):
                    print >> f, '%d,%d,%s,%s' % (
                        seg.bounds[j].x+seg.bounds[j].width//2,
                        seg.bounds[j].y+seg.bounds[j].height//2,
                        calls[j] or '',
                        manual_calls[j] or '',
                        )

            for k, label in enumerate(config.labels):
                for item in calls:
                    if item == label:
                        counts[i][k] += 1
                for item in manual_calls:
                    if item == label:
                        manual_counts[i][k] += 1
        
        for filename,matrix in [
            ('totals.csv', counts),
            ('manual_totals.csv', manual_counts),
            ]:
            with open(work/filename,'wb') as f:
                print >> f, 'image,' + ','.join(config.labels)
                for i, name in enumerate(work.index):
                    print >> f, name+','+','.join(str(item) for item in matrix[i])
        






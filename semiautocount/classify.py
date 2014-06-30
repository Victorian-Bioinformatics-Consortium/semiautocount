
from sklearn import svm

from nesoni import config

from . import util, autocount_workspace

class Classification(object): pass

@config.help(
    'Classify unlabelled cells based on labelled cells.',
    )
class Classify(config.Action_with_working_dir):
    _workspace_class = autocount_workspace.Autocount_workspace

    training = [ ]

    def run(self):
        work = self.get_workspace()
        config = work.get_config()
        
        training_dirs = [ self.working_dir ] + [
            work.relative_path_as_path(item)
            for item in config.training
            ]
        
        data = [ ]
        labels = [ ]
        
        for dirname in training_dirs:
            trainer = autocount_workspace.Autocount_workspace(dirname, must_exist=True)
            for i in xrange(len(trainer.index)):
                image_labels = trainer.get_labels(i)
                image_measure = trainer.get_measure(i)
                for j in xrange(len(image_labels)):
                    labels.append(image_labels[j])
                    data.append(image_measure.data[j])
        
        label_number = { }
        number_label = [ ]
        for item in labels:
            if item is not None and item not in label_number:
                label_number[item] = len(number_label)
                number_label.append(item)

        training_data = [ ]
        training_number = [ ]
        for i in xrange(len(labels)):
            if labels[i] is not None:
                training_data.append(data[i])
                training_number.append(label_number[labels[i]])
        
        clf = svm.SVC(probability=True)
        clf.fit(training_data, training_number)
        
        for i in xrange(len(work.index)):
            result = Classification()
            image_measure = work.get_measure(i)
            result.columns = number_label
            result.log_p = clf.predict_log_proba(image_measure.data)
            result.call = [
                number_label[max(xrange(len(number_label)),key=lambda i:item[i])]
                for item in result.log_p
                ]
            work.set_classification(i, result)







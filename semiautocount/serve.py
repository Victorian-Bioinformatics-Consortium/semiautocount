"""

Provide a website to examine a set of segmented images,
examine classification,
allow interactive classification.

"""

import socket, os, collections, traceback, random, webbrowser

from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.utils import escape, redirect
from werkzeug.wrappers import Request, Response
import jinja2

from scipy import ndimage
from nesoni import config

import numpy as np

from . import images, autocount_workspace, classify, report, util

def image_response(image):
    return Response(
        images.png_str(image),
        mimetype='image/png',
        )


def select_interesting(work, n):
    seen = [ ]
    candidates = [ ]
    
    for i in xrange(len(work.index)):
        print i
        measure = work.get_measure(i)
        labels = work.get_labels(i)
        for j in xrange(len(labels)):
            datum = measure.data[j]
            if labels[j] is None:
                candidates.append([1e30,i,j,datum])
            else:
                seen.append(datum)

    def see(datum):
        for item in candidates:
            offset = datum-item[3]
            d = np.sum(offset*offset)
            item[0] = min(item[0],d)
    
    if len(seen) > 100:
        random.shuffle(seen)
        seen = seen[:100]
    for item in seen: 
        print item
        see(item)
    
    result = [ ]
    for i in xrange(n):
        if not candidates: break
        candidates.sort()
        item = candidates.pop()
        result.append((item[1],item[2]))
        see(item[3])
    return result
     
        



url_map = Map([
    Rule('/cell_image/<int:image_id>/<int:cell_id>', endpoint='on_cell_image'),
    Rule('/cell/<int:image_id>/<int:cell_id>', endpoint='on_cell'),
    Rule('/image_image/<int:image_id>', endpoint='on_image_image'),
    Rule('/image/<int:image_id>', endpoint='on_image'),
    Rule('/find_cell/<int:image_id>', endpoint='on_find_cell'),
    Rule('/classify', endpoint='on_classify'),
    Rule('/next', endpoint='on_next'),
    Rule('/', endpoint='on_home'),
    ])

class Server(object):
    def __init__(self, dirname):
        self.work = autocount_workspace.Autocount_workspace(dirname, must_exist=True)
        conf = self.work.get_config()
        self.labels = conf.labels
        
        self.message = ''
        
        loader = jinja2.FileSystemLoader(
            os.path.join(os.path.split(__file__)[0],'templates')
            )
        self.env = jinja2.Environment(
            loader=loader, 
            line_statement_prefix='#', 
            line_comment_prefix='##',
            )
        self.env.globals['labels'] = self.labels
        self.env.globals['dir_name'] = self.work.name
        
        self.interesting = [ ]

    
    @Request.application
    def application(self, request):
        adapter = url_map.bind_to_environ(request.environ)
        try:
            endpoint, args = adapter.match()
            return getattr(self, endpoint)(request, **args)
            #return Response('hello world: '+endpoint+repr(args))
        except HTTPException, e:
            #print 'Exception:', e
            return e

    def serve(self, open_browser=True):
        from wsgiref.simple_server import make_server
        n = 8000
        while True:
            assert n < 9000, 'Can\'t open a socket.'
            try:
                httpd = make_server('localhost', n, self.application)
                break
            except socket.error:
                n += 1
        self.url = 'http://localhost:%d' % n

        print
        print self.url
        print
        print 'Ctrl-C to shut down.'
        print
        
        try:
            if open_browser:
                webbrowser.open(self.url, new=1)
        
            httpd.serve_forever()
        finally:
            del self.url
    
    def _response(self, template, vars):
        return Response(
            self.env.get_template(template).render(vars),
            mimetype='text/html'
            )
    
            
    def on_cell_image(self, request, image_id, cell_id):
        image = self.work.get_image(image_id)
        seg = self.work.get_segmentation(image_id)
        bound = seg.bounds[cell_id].padded(20)
        result = bound.get(image,[1.,1.,1.])
        mask = bound.get(seg.labels,-1) == cell_id
        #border = images.dilate(mask,2) & ~mask
        result[~mask] *= 0.75
        return image_response(result)
    
    def on_cell(self, request, image_id, cell_id):
        auto = int(request.args.get('auto','0'))
    
        new_label = request.args.get('label',None)
        if 'key' in request.args:
            new_label = chr(int(request.args['key']))
        if new_label and new_label not in self.labels:
            new_label = None
        
        if new_label is not None:
            labels = self.work.get_labels(image_id)
            if new_label == '':
                labels[cell_id] = None
            else:
                labels[cell_id] = new_label
            self.work.set_labels(image_id, labels)
            if auto:
                return redirect('/next')
            return redirect('/image/%d' % image_id)
            #return redirect('/cell/%d/%d' % (image_id, cell_id))
        
        image_name = self.work.index[image_id]
        current_label = self.work.get_labels(image_id)[cell_id]
        
        measure = self.work.get_measure(image_id)        
        
        if not self.work.has_classification(image_id):
            call = None
        else:
            c = self.work.get_classification(image_id)
            call = c.call[cell_id]
    
        return self._response('cell.html', locals())

    @util.cached_named(1, 'image_id')
    def on_image_image(self, image_id):
    #def on_image_image(self, request, image_id):
        result = self.work.get_image(image_id).copy()
        seg = self.work.get_segmentation(image_id)
        border = ndimage.maximum_filter(seg.labels,size=(3,3)) != ndimage.minimum_filter(seg.labels,size=(3,3))
        result[border] = 0.0
        
        return image_response(result)
    
    def on_image(self, request, image_id):
        name = self.work.index[image_id]
        
        seg = self.work.get_segmentation(image_id)
        labels = self.work.get_labels(image_id)
        
        #if not self.work.has_classification(image_id):
        #    calls = [ None ] * len(labels)
        #else:
        #    calls = self.work.get_classification(image_id).call
        calls = self.work.get_calls(image_id, True, False)
        
        label_points = [ ]
        for i, (label, call, bound) in enumerate(zip(labels,calls, seg.bounds)):
            #if label is None: continue
            label_points.append((i,bound.x+bound.width//2,bound.y+bound.height//2,label or '',call or ''))
        
        return self._response('image.html', locals())
    
    def on_home(self, request):
        message = self.message
        self.message = ''
        
        index = self.work.index
        counts = [ [0]*len(self.labels) for i in xrange(len(index)) ]
        manual_counts = [ [0]*len(self.labels) for i in xrange(len(index)) ]
        for i in xrange(len(index)):
            calls = self.work.get_calls(i, True, True)
            manual_calls = self.work.get_calls(i, False, True)
            for j, label in enumerate(self.labels):
                for item in calls:
                    if item == label:
                        counts[i][j] += 1
                for item in manual_calls:
                    if item == label:
                        manual_counts[i][j] += 1  
           
        return self._response('home.html', locals())

    def on_find_cell(self, request, image_id):
        x,y = request.args.keys()[0].split(',')
        x = int(x)
        y = int(y)
        seg = self.work.get_segmentation(image_id)
        cell_id = seg.labels[y,x]
        if cell_id == -1:
            return redirect('/image/%d' % image_id)
        return redirect('/cell/%d/%d' % (image_id,cell_id))
    
    def on_classify(self, request):
        try:
            classify.Classify(self.work.working_dir).run()
            self.message = 'Classified.'
        except:
            traceback.print_exc()
            self.message = 'Classifier failed.'
            
        # In any case, generate output files
        report.Report(self.work.working_dir).run()
        
        return redirect('/')

    def on_next(self, request):
        if not self.interesting:
            self.interesting = select_interesting(self.work, 10)
        if not self.interesting:
            self.message = 'No more cells to classify.'
            return redirect('/')
        image_id, cell_id = self.interesting.pop(0)
        return redirect('/cell/%d/%d?auto=1' % (image_id,cell_id))




@config.help(
    'Interactively label cells.',
    'Starts a local web server which you can interact with '
    'in your web browser.'
    '\n\n'
    'Note: The BROWSER environment variable '
    'can be used to control the choice of browser '
    'as described in '
    'https://docs.python.org/2/library/webbrowser.html'
    )
@config.Bool_flag('browser', 'Open web browser.')
class Label(config.Action_with_working_dir):
    _workspace_class = autocount_workspace.Autocount_workspace
    
    browser = True

    def run(self):
        try:
            Server(self.working_dir).serve(self.browser)
        except KeyboardInterrupt:
            pass






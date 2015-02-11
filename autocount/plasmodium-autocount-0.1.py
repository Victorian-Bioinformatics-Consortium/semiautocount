#!/usr/bin/env python

#    Copyright (C) 2010 Monash University
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


"""

Identify red blood cells and red blood cells infected with plasmodium in a set of images.

"""

import sys, Image, numpy, os, random
from scipy import ndimage

Help = """

Usage:

    python %s [parameter adjustments] <image_directory>

Images should be in TIFF, PNG, or BMP format.

Results will be placed in a new directory named <image_directory>_output.

If the images were annotated using Cell Counting Aid, the hand annotations 
will be shown as circles in the output.

Parameter adjustments take the form

  variable_name=value

See the top of the source code for parameters and their default values.
These have been tuned for our microscope setup, optimal parameters for
your setup may differ.

"""

# How many subprocesses to run at once
N_processors = 1

# ===========
# Diagnostics
#
# What to show in diagnostic output images

Show_edges = False
Show_stain = False
Show_infection = False

Show_hand_marks = True
Show_computer_marks = True
Show_cell_shapes = False


# =================
# Image scaling

Resize_width = 680
Resize_height = 512


# ==========================================
# Image enhancement and fg/bg discrimination
#
# Blur slightly to reduce noise, and unsharp-mask
#
# gaussian_blur(image, a) - b * gaussian_blur(image, c)

Enhance_a = 1.0
Enhance_b = 0.75
Enhance_c = 20.0

# Larger = enlarge background area, smaller = enlarge foreground area
Background_weight = 0.915 #&median


# =============================
# Stain and infection detection

Dark_stain_level = 0.839

Stain_level = 0.9
Stain_bg_blur = 10.0
Stain_spread_required = 3.0

Infection_level = 0.762
Infection_bg_blur = 2.0
Infection_pixels_required = 1



# ====================
# Cell size parameters

# Size of cells, for Hough transform
Hough_min_radius = 5  
Hough_max_radius = 20 

# Portion of cell used for classification as infected/weird
# (may be abutting an infected cell, so be cautious)
# (as a proportion of the true radius)
Cell_inside_radius = 0.9

# Do not allow another cell center to be detected within this radius
Cell_suppression_radius = 1.25


# =======================
# Peculiar cell filtering

# White blood cells appear to be composed entirely of dark staining, filter them out
Max_dark_stain_proportion = 0.728

# Minimum/maximum radius (as determined by Hough transform)
Min_cell_radius = 9
Max_cell_radius = 20

# Proportion of radius that center of mass can be away from Hough determined center
Max_offcenter = 0.5






_offset_cache = { }
def offsets(inner_radius, outer_radius):
    """
    Generate a list of offsets for pixels within a circular region
    """
    
    key = (inner_radius,outer_radius)
    if key not in _offset_cache:
        result = [ ]
        int_radius = int(outer_radius)+1
        for y in xrange(-int_radius,int_radius+1):
            for x in xrange(-int_radius,int_radius+1):
                if inner_radius*inner_radius <= y*y+x*x <= outer_radius*outer_radius:
                    result.append((y,x))
        _offset_cache[key] = numpy.array(result)
    return _offset_cache[key]


def clipped_coordinates(inner_radius,outer_radius, y,x, height,width):
    """
    Coordinates contained within a ring or circle, clipped to rectangular bounds.
    """

    coords = offsets(inner_radius,outer_radius) + [[y,x]]
    valid = (
        (coords[:,0] >= 0) &
        (coords[:,0] < height) &
        (coords[:,1] >= 0) &
        (coords[:,1] < width)
    )
    return coords[valid]

           
def set(array, y, x, value):
    """
    Set an element of an array, if it is in bounds, otherwise silently do nothing
    """

    if y >= 0 and x >= 0 and y < array.shape[0] and x < array.shape[1]:
        array[y,x] = value


def mark_hand(array, filename_in):
    """    
    If there is a file of hand marked cells from Cell Counting Aid, mark them.    
    """

    hand_name = os.path.splitext(filename_in)[0] + '.txt'
    if not os.path.exists(hand_name): return
    
    f = open(hand_name,'rU')
    
    #Skip header line
    f.readline()
    
    for line in f:
        parts = line.rstrip('\n').split(',')
        x,y,infected = parts[:3]
        
        x = int( int(x)/1005.0*array.shape[1] +0.5)
        y = int( int(y)/592.0*array.shape[0] +0.5)
        if infected == 'True':
            if len(parts) == 3:
                color = (196,0,0)
            else:
                infection_type = parts[3]
                if infection_type == '1':
                    color = (196, 196, 0)
                elif infection_type == '3':
                    color = (196, 0, 0)
                else:
                    raise Exception('Unknown infection type')            
        else:
            color = (0,0,196)
        for i in (-2,-1,0,1,2):
            set(array,y-3,x+i,color)
            set(array,y+3,x+i,color)
            set(array,y+i,x-3,color)
            set(array,y+i,x+3,color)


def gaussian_blur(array, amount):
    """
    Gaussian blur each channel of a color image.
    """
    output = numpy.empty(array.shape, array.dtype)
    for i in xrange(array.shape[2]):
        ndimage.gaussian_filter(array[:,:,i],amount,output=output[:,:,i])
    return output


def status(word):
    pass
    #sys.stdout.write(word+' ')
    #sys.stdout.flush()


def process(filename_in, filename_out, filename_coords, name):
    # Load image
    i = Image.open(filename_in)

    print 'Processing', filename_in, '->', filename_out

    # Resize (mostly done for speed increase)
    i = i.resize((Resize_width,Resize_height), Image.ANTIALIAS)

    # Convert to numpy array
    a = numpy.asarray(i).astype('float64')
    height = a.shape[0]
    width = a.shape[1]

    a_gray = numpy.sum(a, 2)
    
    # Make a copy of the array to doodle various diagnostic markings on
    a_output = a.copy()    

    # If there are hand-marked cells, show them in the output image
    if Show_hand_marks:
        mark_hand(a_output, filename_in)    


    # Denoise/unsharp mask
    a_enhanced = gaussian_blur(a, Enhance_a) - Enhance_b*gaussian_blur(a,Enhance_c)
    
    
    # Split into foreground and background using k-medians
    status('fg/bg')
    
    a_raveled = numpy.reshape(a_enhanced,(width*height,a_enhanced.shape[2]))
    average = numpy.average(a_raveled, axis=0)
    # Initial guess
    color_bg = average*1.5
    color_fg = average*0.5
    
    for i in xrange(5):
        d_bg = a_raveled-color_bg[None,:]
        d_bg *= d_bg
        d_bg = numpy.sum(d_bg,1)
        d_fg = a_raveled-color_fg[None,:]
        d_fg *= d_fg
        d_fg = numpy.sum(d_fg,1)
        fg = d_fg*Background_weight < d_bg
        color_fg = numpy.median(a_raveled[fg,:],axis=0)
        color_bg = numpy.median(a_raveled[~fg,:],axis=0)
        
    fg = numpy.reshape(fg, (height,width))
    
    edge = ndimage.maximum_filter(fg,size=3) != ndimage.minimum_filter(fg,size=3)

    d_fg = numpy.sqrt(numpy.reshape(d_fg, (height,width)))
    d_bg = numpy.sqrt(numpy.reshape(d_bg, (height,width)))
    
    # Staining is taken as foreground pixels that differ markedly from the mean foreground color
    # (also, they must be darker in the red and green channels)
    # The background intensity is simply a useful basis for scaling
    # (should be invariant under changes in brightness) 
    mag_bg = numpy.average(color_bg)
    
    dark_stain = (
        (d_fg > mag_bg*Dark_stain_level) &
        (a_enhanced[:,:,0] < color_fg[0]) & 
        (a_enhanced[:,:,1] < color_fg[1]) &
        fg
    )
    
    
    fg_float = fg.astype('float64')
    green = a[:,:,1] * fg_float
    green_local_bg = ndimage.gaussian_filter(green, Stain_bg_blur)
    green_local_bg_divisor = ndimage.gaussian_filter(fg_float, Stain_bg_blur)
    stain = (
        (green * green_local_bg_divisor < green_local_bg * Stain_level) &
        fg 
    ) 
        
    # Detect infection as lumpiness in the green channel (green is most affected by staining)
    # Must also be within a stained region
    green_local_bg = ndimage.gaussian_filter(green, Infection_bg_blur)
    green_local_bg_divisor = ndimage.gaussian_filter(fg_float, Infection_bg_blur)
    infection = (
        (green * green_local_bg_divisor < green_local_bg * Infection_level) &
        stain
    ) 
        
    # Show edges and infection on output image
    if Show_edges:
        a_output[edge,:] += 64
    if Show_stain:
        a_output[stain,2] += 128
    if Show_infection:
        a_output[infection,0] += 128
        
        
    # Hough transform
    status('hough')
    
    x_edge = ndimage.convolve(a_gray,
        [[-1,0,1],
         [-2,0,2],
         [-1,0,1]])    
    y_edge = ndimage.convolve(a_gray,
        [[-1,-2,-1],
         [0,0,0],
         [1,2,1]])
    mag = numpy.sqrt(x_edge*x_edge+y_edge*y_edge)
    x_dir = x_edge / mag
    y_dir = y_edge / mag

    # Vectorized for enhanced performance and incomprehensibility:
    ys = []
    xs = []
    for y in xrange(height):
        for x in xrange(width):
            if edge[y,x]:
               ys.append(y)
               xs.append(x)
    ys = numpy.array(ys)
    xs = numpy.array(xs)
    indexes = numpy.arange(len(ys))

    def do_hough(radius):
        hough = numpy.zeros((height,width), 'float64')
        
        oys = (ys + y_dir[ys,xs]*radius + 0.5).astype('int')
        oxs = (xs + x_dir[ys,xs]*radius + 0.5).astype('int')
        valid = (
            (oys >= 0) &
            (oys < height) &
            (oxs >= 0) &
            (oxs < width)
        )
        for i in indexes[valid]:
            hough[oys[i],oxs[i]] += 1.
        
        #for y in xrange(height):
        #    for x in xrange(width):
        #        if edge[y,x]:
        #            oy = y + y_dir[y,x]*radius
        #            ox = x + x_dir[y,x]*radius
        #            ioy = int(oy+0.5)
        #            iox = int(ox+0.5)
        #            if ioy>0 and iox>0 and ioy<height and iox<width:
        #                hough[ioy,iox] += 1.                        
        
        # Blur the transformed image a little
        # (more blurring allows greater deviation from circularity)
        # (if you alter this you will also need to alter thresh, below)
        
        hough = ndimage.gaussian_filter(hough, 1.0)
        
        return hough

    hough = numpy.zeros((height,width),'float64')
    hough_radius = numpy.zeros((height,width),'int')
    for i in xrange(Hough_min_radius,Hough_max_radius+1):
        #print 'Hough radius', i
        this_hough = do_hough(i)
        better = this_hough > hough
        hough_radius[better] = i
        hough[better] = this_hough[better]

    # Show result of Hough transform in output image
    #a_output[:,:,:] = hough[:,:,None]*20

    # Find and classify peaks in Hough transform image
    thresh = 1.5 #Hmm
    candidates = [ ]
    for y in xrange(height):
        for x in xrange(width):
            if hough[y,x] > thresh:
                candidates.append((hough[y,x],y,x))
    candidates.sort(reverse=True)
    
    status('classify')
    
    file_coords = open(filename_coords,'wt')
    file_coords.write('Autocount on %dx%d image\n' % (width,height))
    
    suppress = numpy.zeros((height,width), 'bool')
    claim_strength = numpy.zeros((height,width), 'float64') + 1e30
    cells = [ ] # [(y,x)]
    n = 0
    n_infected = 0
    n_late = 0
    for _,y,x in candidates:
        radius = hough_radius[y,x]        

        # Make sure candidate is not near a previously detected cell,
        # and does not abut the edge of the image        
        if not suppress[y,x] and \
           y >= radius and x >= radius and y < height-radius and x < width-radius:
            coords = clipped_coordinates(0,radius*Cell_inside_radius, y,x,height,width)
            
            #Only include foreground
            this_fg = fg[coords[:,0],coords[:,1]]
            coords = coords[this_fg]
            
            this_strength = ((coords[:,0]-y)**2 + (coords[:,1]-x)**2)
            claim_strength[coords[:,0],coords[:,1]] = numpy.minimum(
                claim_strength[coords[:,0],coords[:,1]],
                this_strength
            )
            
            cells.append((y,x, coords,this_strength))

           
        # Suppress detection of cells too close to here
        # (note: we do this irrespective of whether we treated this location as a hit)
        
        coords = clipped_coordinates(0,radius*Cell_suppression_radius, y,x,height,width)
        suppress[coords[:,0],coords[:,1]] = True
        
        #for oy, ox in offsets(0, radius*Cell_suppression_radius): #suppression_offsets:
        #    ny = y+oy
        #    nx = x+ox
        #    if ny >= 0 and nx >= 0 and ny < height and nx < width:
        #        suppress[ny,nx] = True

    for y,x, coords, this_strength in cells:            
        radius = hough_radius[y,x]
        
        if not len(coords): continue # No fg pixels within radius
        
        winners = claim_strength[coords[:,0],coords[:,1]] >= this_strength
        coords = coords[winners]
        
        if not len(coords): continue # Did not win any foreground pixels
                
        infected_pixels = 0
        stain_pixels = 0
        dark_stain_pixels = 0
        fg_pixels = 0
        
        stain_x = 0.0
        stain_x2 = 0.0
        stain_y = 0.0
        stain_y2 = 0.0 
        
        for ny, nx in coords:
            if infection[ny,nx]:
                infected_pixels += 1
            if stain[ny,nx]:
                stain_pixels += 1
                
                stain_x += nx
                stain_x2 += nx*nx
                stain_y += ny
                stain_y2 += ny*ny
            if dark_stain[ny,nx]:
                dark_stain_pixels += 1
            fg_pixels += 1

        mass_y = numpy.average(coords[:,0])
        mass_x = numpy.average(coords[:,1])
        mass_offset = numpy.sqrt( (mass_y-y)**2 + (mass_x-x)**2 )
        
        is_infected = (infected_pixels >= Infection_pixels_required and stain_pixels >= 1)
         
        if is_infected:
            stain_spread = (
                stain_x2/stain_pixels - (stain_x/stain_pixels)**2 +
                stain_y2/stain_pixels - (stain_y/stain_pixels)**2
            )
            is_infected = stain_spread >= Stain_spread_required
            
        is_peculiar = (
            (radius > Max_cell_radius) or
            (radius < Min_cell_radius) or
            (mass_offset > Max_offcenter * radius) or
            (dark_stain_pixels >= fg_pixels*Max_dark_stain_proportion)
        )
        
        if is_peculiar:
            color = (0,0,0)
            file_coords.write('%d,%d,Rejected\n' % (x,y))
        elif is_infected:
            n += 1
            n_infected += 1
            color = (255,0,0)
            file_coords.write('%d,%d,Infected\n' % (x,y))
        else:
            n += 1
            color = (0,0,255)
            file_coords.write('%d,%d,Uninfected\n' % (x,y))
        
        # Mark detected cell on output image
        if Show_computer_marks:
            set(a_output,y,x,color)
            for i in xrange(1,3):
                set(a_output,y-i,x,color)  
                set(a_output,y+i,x,color)  
                set(a_output,y,x-i,color)  
                set(a_output,y,x+i,color)

        if Show_cell_shapes:            
            a_output[coords[:,0],coords[:,1]] += [[ random.random()*64+32 for i in (0,1,2) ]]
            
        
    
    file_coords.close()
    
    # Save diagnostic output image
    a_output = numpy.clip(a_output,0,255)
    i2 = Image.fromarray(a_output.astype('uint8'))    
    i2.save(filename_out)
    


def read_ac(filename):
    f = open(filename,'rU')
    f.readline()
    n_total = 0
    n_infected = 0
    for line in f:
        parts = line.rstrip().split(',')
        if parts[2] == 'Uninfected':
            n_total += 1
        elif parts[2] == 'Infected':
            n_total += 1
            n_infected += 1
    
    return n_total, n_infected


if __name__ == '__main__':
    args = sys.argv[1:]
    
    while len(args) > 1:
        name, value = args.pop(0).split('=')
        value = float(value)
        assert hasattr(sys.modules[__name__], name), 'Parameter named %s does not exist' % name
        setattr(sys.modules[__name__], name, value)
        print name, '=', value

    if len(args) != 1:
        print Help % sys.argv[0]
        sys.exit(1)

    if os.path.isfile(args[0]):
        in_dir, filename = os.path.split(args[0])
        filenames = [ filename ]
        is_subprocess = True
        
    else:
        in_dir = args[0]
        filenames = os.listdir(in_dir)
        filenames.sort()
        is_subprocess = False
    
    out_dir = os.path.normpath(in_dir) + '_output'
    if not os.path.exists(out_dir):
       os.mkdir(out_dir)
    
    if not is_subprocess:
        for filename in filenames:
            root, ext = os.path.splitext(filename)
            ac_filename = os.path.join(out_dir, root+'.ac')
            if os.path.exists(ac_filename): os.unlink(ac_filename)
    
    coord_filenames = [ ]
    
    n_running = 0
    
    for filename in filenames:
        root, ext = os.path.splitext(filename)
        if ext.lower() not in ('.bmp','.tif','.tiff','.png'): continue
        
        filename_in = os.path.join(in_dir, filename)
        filename_out = os.path.join(out_dir, root+'.tif')
        filename_coords = os.path.join(out_dir, root+'.ac')
        
        if is_subprocess or N_processors == 1:
            process(filename_in, filename_out, filename_coords, root)
        else:
            while n_running >= N_processors:
                os.wait()
                n_running -= 1
            os.spawnl(os.P_NOWAIT, sys.executable, sys.executable, *(sys.argv[:-1]+[filename_in]))
            n_running += 1
        
        coord_filenames.append((filename_coords, root))

    while n_running:
        os.wait()
        n_running -= 1

    if not is_subprocess:        
        result_file = open(os.path.join(out_dir,'results.txt'),'wt')
        
        for filename_coords, root in coord_filenames:
            n_total, n_infected = read_ac(filename_coords)
            print >> result_file, root, n_total, n_infected
            
        result_file.close()
    
    

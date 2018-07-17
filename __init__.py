import numpy as np
import string
import itertools

def color2rgba(color, opacity=1.0):
    '''convert a color in html (#RRGGBB), rgb or rgba format to rgba with opacity=opacity'''
    if color[0] == '#':
        r = int(color[1:3],16)
        g = int(color[3:5],16)
        b = int(color[5:7],16)
        return 'rgba({},{},{},{})'.format(r,g,b,opacity)
    elif color.startswith('rgba'):
        rgb,o = color.rsplit(',',maxsplit=1)
        return '{},{})'.format(rgb,opacity)
    elif color.startswith('rgb'):
        color = color.strip()
        return 'rgba{},{})'.format(color[3:-1],opacity)
    else:
        raise ValueError("can't figure out color `{}`".format(color))

def scalecolor(color, amount=1.0):
    '''darken a color (if the amount is <1) or lighten it (>1)'''
    o = None
    if color[0] == '#':
        r = int(color[1:3],16)
        g = int(color[3:5],16)
        b = int(color[5:7],16)
    elif color.startswith('rgba'):
        _,color = color.split('(',maxsplit=1)
        color,_ = color.split(')',maxsplit=1)
        r,g,b,o = [float(i) for i in color.split(',')]
    elif color.startswith('rgb'):
        _,color = color.split('(',maxsplit=1)
        color,_ = color.split(')',maxsplit=1)
        r,g,b = [int(i) for i in color.split(',')]
    else:
        raise ValueError("can't figure out color `{}`".format(color))
    
    r,g,b = [int(np.clip(amount * i,0,255)) for i in [r,g,b]]
    if o is not None:
        return 'rgba({},{},{},{})'.format(r,g,b,o)
    else:
        return 'rgb({},{},{})'.format(r,g,b)
    
def getApproximateArialStringWidth(st):
    '''Approximate how long a string will be'''
    size = 0 # in milinches
    for s in st:
        if s in 'lij|\' ': size += 37
        elif s in '![]fI.,:;/\\t': size += 50
        elif s in '`-(){}r"': size += 60
        elif s in '*^zcsJkvxy': size += 85
        elif s in 'aebdhnopqug#$L+<>=?_~FZT' + string.digits: size += 95
        elif s in 'BSPEAKVXY&UwNRCHD': size += 112
        elif s in 'QGOMm%W@': size += 135
        else: size += 50
    return size * 6 / 1000.0 # Convert to picas

class Rect:
    '''A generic rectangle'''
    def __init__(self,x_scale, y_scale, t,r,b,l):
        self.scale = (x_scale, y_scale)
        self.box = (t,r,b,l)
    
    @property
    def x_scale(self): return self.scale[0]
    @property
    def y_scale(self): return self.scale[1]
    
    @property
    def hcenter(self): return (self.right + self.left) * 0.5
    @property
    def vcenter(self): return (self.top + self.bottom) * 0.5
    @property
    def height(self): return (self.top - self.bottom)
    @property
    def width(self): return (self.right - self.left)
    
    @property
    def top(self): return self.box[0]
    @property
    def right(self): return self.box[1]
    @property
    def bottom(self): return self.box[2]
    @property
    def left(self): return self.box[3]
    
    def offset(self, horizontal=0.0, vertical=0.0):
        self.box = (self.box[0]+vertical, self.box[1]+horizontal, self.box[2]+vertical, self.box[3]+horizontal)
        
    @staticmethod
    def overlap(r1,r2):
        hoverlaps = not(r1.left > r2.right) and not(r1.right < r2.left)
        voverlaps = not(r1.top < r2.bottom) and not(r1.bottom > r2.top)
        return hoverlaps and voverlaps
    
    def __repr__(self):
        return '({})'.format(','.join(str(i) for i in self.box))
    
    def as_shape(self, color='rgba(128, 0, 128, 0.7)'):
        return {
            'type': 'rect',
            'x0': self.box[3],
            'y0': self.box[2],
            'x1': self.box[1],
            'y1': self.box[0],
            'line': {
                'width': 0,
            },
            'fillcolor': color,
        }
    
class TextRect(Rect):
    '''A text rectangle'''
    
    M_SQRT_2_OVER_2 = np.sqrt(2) * 0.5
    
    def __init__(self, text, point, *args, color=None):
        self.text = text
        self.point = point
        if color is None:
            self.color = 'rgb(10,10,10)'
        else:
            self.color = scalecolor(color,0.75)
        super().__init__(*args)
    
    def to_side(self, side, dist=1):
        '''Move the text label to the top/bottom/left/right (or combos like topleft) of the point in question.
        `x_off` and `y_off` are the distance to the point'''
        x_scale, y_scale = self.x_scale*dist, self.y_scale*dist
        
        # Angles, multiply by sqrt(2)/2
        if side not in ('top', 'bottom', 'left', 'right'):
            x_scale *= TextRect.M_SQRT_2_OVER_2
            y_scale *= TextRect.M_SQRT_2_OVER_2
            
        if 'top' in side:
            vertical = self.point.top - self.bottom + y_scale
        elif 'bottom' in side:
            vertical = self.point.bottom - self.top - y_scale
        else:
            vertical = self.point.vcenter - self.vcenter
            
        if 'left' in side:
            horizontal = self.point.left - self.right - x_scale
        elif 'right' in side:
            horizontal = self.point.right - self.left + x_scale
        else:
            horizontal = self.point.hcenter - self.hcenter
            
        self.offset(vertical=vertical, horizontal=horizontal)
            
    def dist(self):
        '''Return the distance between the text and the point in pixels (based on scale)'''
        x_scale, y_scale = self.x_scale, self.y_scale
        
        xdist = 1 / x_scale * max(0, np.abs(self.point.hcenter - self.hcenter) - ((self.point.width + self.width)*0.5))
        ydist = 1 / y_scale * max(0, np.abs(self.point.vcenter - self.vcenter) - ((self.point.height + self.height)*0.5))
        return np.sqrt(xdist**2 + ydist**2)
    
    def as_annotation(self, fontsize=12, arrowhead=0, opacity=0.8):
        '''Return my annotation'''
        d = self.dist()
        if d < 2.0:
            opac = 0.0
        else:
            opac = 0.25
        return dict(
            x=self.point.hcenter,  y=self.point.vcenter,
            ax=self.hcenter, ay=self.vcenter,
            xref='x', yref='y', axref='x', ayref='y',
            text=self.text,
            showarrow=True,
            arrowhead=arrowhead,
            opacity=opacity,
            arrowcolor=color2rgba(self.color, opac),
            font=dict(
                size=fontsize,
                color=self.color,
            ),
        )
    
class RectMaker:
    '''Makes rectangles for us, storing our scale/fontsizes'''
    def __init__(self, x_scale, y_scale, fontsize):
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.fontsize = fontsize
        
    def center_box(self, x, y, wpx, hpx):
        '''create a box given a center point and a width/heigh'''
        w = wpx * self.x_scale * 0.5
        h = hpx * self.y_scale * 0.5
        return Rect(self.x_scale, self.y_scale, y+h,x+w,y-h,x-w)
        
    def text_box(self, point, text, side='top',color=None):
        '''create a text box relative to the Rect object `point` with the text `text`.
        Use side to control where the text is initially placed'''
        x,y = point.hcenter, point.vcenter
        f_height = self.fontsize
        text_width = getApproximateArialStringWidth(text) * self.fontsize * 1.1
        w = text_width * self.x_scale * 0.5
        h = f_height * self.y_scale * 0.5
        tr = TextRect(text, point, self.x_scale, self.y_scale, y+h,x+w,y-h,x-w, color=color)
        tr.to_side(side)
        return tr
        
def non_overlap_text_boxes(x,y,markersize,text,fontsize,width_px,height_px,xrange,yrange,color=None):
    '''Create non overlapping text boxes (TextRect objects). Width/height are in pixels.
    x/yrange are in data units (as are x/y). Markersize is in pixels, as is fontsize.'''
    
    # Scale between values and pixels
    x_scale = xrange / width_px
    y_scale = yrange / height_px
    
    # A simple class to create our box objects
    rm = RectMaker(x_scale, y_scale, fontsize)
    
    # Make sure it is an array so we can iterate over it
    if not hasattr(markersize, '__len__'):
        markersize = itertools.repeat(markersize)
    if not hasattr(color, '__len__'):
        color = itertools.repeat(color)
        
    # Create the boxes for the markers (fixed location)
    boxes = [rm.center_box(x_,y_,s_,s_) for (x_,y_,s_) in zip(x,y,markersize)]
    
    # Create the text boxes (variable location)
    text_boxes = [rm.text_box(b_,t_,color=c_) for (b_,t_,c_) in zip(boxes,text,color)]
    
    # Our algorithm for placement is to take each point and swing it around the cardinal directions
    # moving it progressively further and further out. If it ever fits at a given point without
    # overlap, lock it there.
    step = min(width_px,height_px) * 0.01
    
    bad = text_boxes
    for iteration in range(10):
        
        # Distance to move for this iteration
        dist = (1+iteration*step)
        
        # Loop over all badly placed text boxes
        for t in bad:
            
            # Loop over each side of the point
            overlaps = True
            for side in ('top','bottom','right','left','topright','bottomright','bottomleft','topleft'):
                
                # Try moving then check for overlap. If it has no overlaps, lock it down and move on
                t.to_side(side, dist)
                overlaps = any(Rect.overlap(t,b) for b in boxes + text_boxes if t is not b)
                if not overlaps:
                    break
            
            # If it still overlaps, move it back to the top to start again
            if overlaps:
                t.to_side('top', dist)
        
        # Find all badly placed text boxes
        bad = [t for t in text_boxes if any(Rect.overlap(t,b) for b in boxes + text_boxes if t is not b)]
        
        # Exit if we've placed all text boxes without overlap
        if not bad:
            break
    
    return text_boxes

def non_overlap_annotations(x,y,markersize,text,fontsize,width_px,height_px,xrange,yrange,color=None):
    '''Create non overlapping text annotations. Width/height are in pixels.
    x/yrange are in data units (as are x/y). Markersize is in pixels, as is fontsize.'''
    text_boxes = non_overlap_text_boxes(x,y,markersize,text,fontsize,width_px,height_px,xrange,yrange,color=color)
    return [i.as_annotation(fontsize=fontsize) for i in text_boxes]

def _get_range(x, axis):
    '''internal method: create a range if none exists'''
    rng = axis['range']
    if rng is None:
        rng = [np.min(x), np.max(x)]
        margin = (rng[1] - rng[0]) * 0.1
        rng = [rng[0] - margin, rng[1] + margin]
        axis.update(autorange=False, range=rng)
    return np.abs(rng[1] - rng[0])

def plotly_non_overlap_text(scatter, layout):
    '''Generate non-overlapping text annotations given a scatter plot object and a layout object.
    
    The scatter object must set the x, y and text attributes. This function will use the marker/size
    and textfont/size parameters. Otherwise it will set default values for these.
    
    This function will use the x(y)axis/range values, width/height, and margin (t,b,l,r) if they are
    set in the layout object. Otherwise it will set default values.
    
    The layout and scatter objects will be modified in place with any missing values from above.
    The layout will also have the `annotations` key filled in the with annotation objects.
    
    This function returns the modified scatter/layout objects.
    '''
    
    # Load width/height and margins, setting default values if none are present
    margin = layout['margin']
    width_px = layout.setdefault('width',1000) - margin.setdefault('l',50) - margin.setdefault('r',50)
    height_px = layout.setdefault('height',600) - margin.setdefault('t',50) - margin.setdefault('b',50)
    
    # Load values from the scatter, setting defaults for the markers if 
    x = scatter['x']
    y = scatter['y']
    text = scatter['text']
    markersize=scatter['marker'].setdefault('size', np.ones(len(x)) * 10)
    fontsize = scatter['textfont'].setdefault('size', np.round(.015 * layout['height']))
    color = scatter['marker'].get('color',None)
    
    xrange = _get_range(x, layout['xaxis'])
    yrange = _get_range(y, layout['yaxis'])
    
    # Call the generic function to generate non-overlapping labels
    anno = non_overlap_annotations(x,y,markersize,text,fontsize,width_px,height_px,xrange,yrange,color=color)
    
    # Add them to the layout
    layout.update(annotations=anno)
    
    return scatter, layout
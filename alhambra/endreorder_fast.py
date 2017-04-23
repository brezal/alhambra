# End reordering code to optimize placement.

from . import anneal
from . import sensitivity as sens
import stickydesign as sd
import stickydesign.energetics as en
import numpy.random as random
import numpy as np
import random as pyrand
from copy import deepcopy
import numpy.ma as ma

def flatten(seq):
    for item in seq:
        if is_string_like(item) or not iterable(item):
            yield item
        else:
            for subitem in flatten(item):
                yield subitem

def ecomp(x):
    if x[-1]=='/':
        return x[:-1]
    else:
        return x+'/'

class FseqState:
    def __init__(self, seqs=None):
        if not seqs:
            self.seqs = {}
        else:
            self.seqs = seqs
    def copy(self):
        return FseqState({'DT': self.seqs['DT'].copy(), 'TD': self.seqs['TD'].copy()})

class cachedarray:
    def __init__(self, func, shape):
        self.arr = ma.masked_all(shape)
        self.func = func
    def __getitem__(self, index):
        if self.arr.mask[index]:
            self.arr[index] = self.func(*index)
        return self.arr[index]

from copy import deepcopy
class FastState:
    def __init__(self, state):
        self.state = state
    def copy(self):
        return deepcopy(self)
    def __getitem__(self, it):
        return self.state[it]


class EndSystemFseq:
    def __init__(self, tilesys, pairs=None, energetics=None):
        # Set up variables, etc.
        if not energetics:
            self.ef = en.energetics_santalucia(mismatchtype='max')
        else:
            self.ef = energetics
        tilesys = deepcopy(tilesys)
        self.ends = tilesys['ends']
        self.tiles = tilesys['tiles']
        self.tilesystem = tilesys
        
        if not pairs:
            pairs = sens.consolidate_pairs( sens.senspairs(tilesys), comcomp=1, onlytop=True )

        self.names = {}
        fseqsTD, self.names['TD'] = (list(x) for x in zip(*[ [end['fseq'].lower(),end['name']] for end in self.ends if end['type'] == 'TD']))
        fseqsDT, self.names['DT'] = (list(x) for x in zip(*[ [end['fseq'].lower(),end['name']] for end in self.ends if end['type'] == 'DT']))
        self.seqs = {}
        self.seqs['TD'] = sd.endarray(fseqsTD,'TD')
        self.seqs['DT'] = sd.endarray(fseqsDT,'DT')
        self.initstate = FastState({'DT': np.arange(0,len(self.seqs['DT'])), 'TD': np.arange(0,len(self.seqs['TD']))})
        self.enlocs = {}
        for i, endn in enumerate(self.names['TD']):
            self.enlocs[endn] = (i,'TD')
        for i, endn in enumerate(self.names['DT']):
            self.enlocs[endn] = (i,'DT')        
        
        # Get the mean non-spurious interaction
        self.meangse = 0.5*( np.mean(self.ef.matching_uniform( self.seqs['TD'] ))+np.mean(self.ef.matching_uniform( self.seqs['DT'] )) )
        self.mult = {'1NGO': np.exp(-2.0*self.meangse), '2NGO': np.exp(-1.65*self.meangse), '1GO': np.exp(-1.5*self.meangse), '2GO': np.exp(-1.1*self.meangse)}
        
        self.pairdict = {}
        for pairclass,memberset in pairs.items():
            for x,y in memberset:
                self.pairdict[(x,ecomp(y))] = pairclass
                self.pairdict[(y,ecomp(x))] = pairclass
        tdsh = ( len(self.seqs['TD']), len(self.seqs['TD']) )
        dtsh = ( len(self.seqs['DT']), len(self.seqs['DT']) )
        self.ecache_cc = {  'TD': cachedarray( lambda x,y: self.ef.uniform(self.seqs['TD'][x:x+1].comps,self.seqs['TD'][y:y+1].comps) , tdsh ),
                            'DT': cachedarray( lambda x,y: self.ef.uniform(self.seqs['DT'][x:x+1].comps,self.seqs['DT'][y:y+1].comps) , dtsh ) }
        self.ecache_ce = {  'TD': cachedarray( lambda x,y: self.ef.uniform(self.seqs['TD'][x:x+1].comps,self.seqs['TD'][y:y+1].ends) , tdsh ),
                            'DT': cachedarray( lambda x,y: self.ef.uniform(self.seqs['DT'][x:x+1].comps,self.seqs['DT'][y:y+1].ends) , dtsh ) }
        self.ecache_ec = {  'TD': cachedarray( lambda x,y: self.ef.uniform(self.seqs['TD'][x:x+1].ends,self.seqs['TD'][y:y+1].comps) , tdsh ),
                            'DT': cachedarray( lambda x,y: self.ef.uniform(self.seqs['DT'][x:x+1].ends,self.seqs['DT'][y:y+1].comps) , dtsh ) }
        self.ecache_ee = {  'TD': cachedarray( lambda x,y: self.ef.uniform(self.seqs['TD'][x:x+1].ends,self.seqs['TD'][y:y+1].ends) , tdsh ),
                            'DT': cachedarray( lambda x,y: self.ef.uniform(self.seqs['DT'][x:x+1].ends,self.seqs['DT'][y:y+1].ends) , dtsh ) }
    def slowseqs(self, state):
        "Give the state as the slow version would have"
        return {'DT': self.seqs['DT'][state['DT']], 'TD': self.seqs['TD'][state['TD']] }

    def mutate(self, state):
        # Start by deciding to swap TD or DT ends.
        if random.rand() > 1.0*len(state['TD'])/(len(state['DT'])+len(state['TD'])):
            t = 'DT'
        else:
            t = 'TD'
        
        en = len(state[t])
        
        a = random.randint( 0, en )
        b = random.randint( 0, en )
        state[t][[a,b]] = state[t][[b,a]]

    def score(self, state):
        
        sc = 0.0
        
        for (xn,yn),pairclass in self.pairdict.items():
            
            # set comp flags
            xc = False
            yc = False
            if xn[-1] == '/':
                xc = True
                xn = xn[:-1]
            if yn[-1] == '/':
                yc = True
                yn = yn[:-1]
                
            # get end indexes and types
            xi,xt = self.enlocs[xn]
            yi,yt = self.enlocs[yn]
            #print "%s, %s: (%s %s)" % (xn,yn,xt,yt)
            # skip if not same type
            if xt != yt: continue
            
            if yc and xc:
                val = self.ecache_cc[xt][state[xt][xi],state[yt][yi]] # self.ef.uniform(state.seqs[xt][xi:xi+1].comps,state.seqs[yt][yi:yi+1].comps)[0]
            elif xc:
                val = self.ecache_ce[xt][state[xt][xi],state[yt][yi]] # self.ef.uniform(state.seqs[xt][xi:xi+1].comps,state.seqs[yt][yi:yi+1].ends)[0]
            elif yc:
                val = self.ecache_ec[xt][state[xt][xi],state[yt][yi]] # state[f.uniform(state.seqs[xt][xi:xi+1].ends,state.seqs[yt][yi:yi+1].comps)[0]
            else:
                val = self.ecache_ee[xt][state[xt][xi],state[yt][yi]] # self.ef.uniform(state.seqs[xt][xi:xi+1].ends,state.seqs[yt][yi:yi+1].ends)[0]
            
            sc += self.mult[pairclass]*np.exp( val )
    
        return sc   

            
wcd = {   'a': 't',
         'b': 'v',
         'c': 'g',
         'd': 'h',
         'g': 'c',
         'h': 'd',
         'k': 'm',
         'm': 'k',
         'n': 'n',
         's': 's',
         't': 'a',
         'v': 'b',
         'w': 'w' }
         
def wc(seqstr):
    return ''.join(wcd[x] for x in reversed(seqstr))
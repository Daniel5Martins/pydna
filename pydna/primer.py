#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2013, 2014 by Björn Johansson.  All rights reserved.
# This code is part of the Python-dna distribution and governed by its
# license.  Please see the LICENSE.txt file that should have been included
# as part of this package.

'''
This module contain functions for primer design.

'''
from Bio.Alphabet.IUPAC import IUPACAmbiguousDNA  as _IUPACAmbiguousDNA
from Bio.Seq import Seq                           as _Seq
from Bio.SeqRecord import SeqRecord               as _SeqRecord
from pydna.tm import tmbresluc                    as _tmbresluc

class Primer(_SeqRecord):
    '''This class can hold information about a primer and its position on a template 
       footprint and tail.   
    
    '''
    def __init__(self, record, 
                 *args,
                 template =  None,
                 position =  None, 
                 footprint = None,
                 concentration = 1000.0,   # nM (= 1µM)
                 **kwargs):
        if hasattr(record, "features"):
            for key, value in record.__dict__.items():
                setattr(self, key, value )
        elif hasattr(record, "alphabet"):
            super().__init__(record, *args, **kwargs)            
        else:        
            super().__init__(_Seq(record, _IUPACAmbiguousDNA()), *args, **kwargs)
        self.concentration = concentration           
        self.position      = position
        self._fp           = footprint
        self.template      = template
    
    @property
    def footprint(self):
        return self.seq[-self._fp:] if self._fp else ""

    @property
    def tail(self):
        return self.seq[:-self._fp] if self._fp else ""

    def __repr__(self):
        s = min( (self.seq,"{}..{}".format(self.seq[:15], self.seq[-3:])), key=len)
        return "{id} {len}-mer:5'-{seq}-3'".format(id=self.id,len=len(self),seq=s)
    
    def __radd__(self, other):
        new = super().__radd__(other)
        return Primer(new, template = self.template, position=self.position, footprint=self._fp)
    
    def tm(self, saltc=50.0, formula=_tmbresluc):
        return formula( str(self.seq).upper(), primerc=self.concentration, saltc=saltc )

if __name__=="__main__":
    import os as _os
    cache = _os.getenv("pydna_cache", "nocache")
    _os.environ["pydna_cache"]="nocache"
    import doctest
    doctest.testmod(verbose=True, optionflags=doctest.ELLIPSIS)
    _os.environ["pydna_cache"]=cache

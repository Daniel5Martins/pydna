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
import math                                       as _math
from operator import itemgetter                   as _itemgetter
from Bio.Alphabet import Alphabet                 as _Alphabet
from Bio.Alphabet.IUPAC import IUPACAmbiguousDNA  as _IUPACAmbiguousDNA
from Bio.Seq import Seq                           as _Seq
from pydna.amplify import Anneal                       as _Anneal
from pydna.tm import tmbresluc                         as _tmbresluc
from pydna.dseqrecord import Dseqrecord                as _Dseqrecord
from pydna._pretty import pretty_str                   as _pretty_str
from pydna.primer    import Primer                     as _Primer


def print_primer_pair(*args,**kwargs):
    f,r = cloning_primers(*args,**kwargs)
    return _pretty_str("\n"+f.format("fasta")+"\n"+r.format("fasta") + "\n")

def cloning_primers( template,
                     minlength=16,
                     maxlength=29,
                     fp=None,
                     rp=None,
                     fp_tail='',
                     rp_tail='',
                     target_tm=55.0,
                     fprimerc=1000.0,
                     rprimerc=1000.0,
                     saltc=50.0,
                     formula = _tmbresluc):

    '''This function can design primers for PCR amplification of a given sequence.
    This function accepts a Dseqrecord object containing the template sequence and
    returns a tuple cntaining two ::mod`Bio.SeqRecord.SeqRecord` objects describing
    the primers.

    Primer tails can optionally be given in the form of strings.

    An predesigned primer can be given, either the forward or reverse primers. In this
    case this function tries to design a primer with a Tm to match the given primer.


    Parameters
    ----------

    template : Dseqrecord
        a Dseqrecord object. The only required argument.

    minlength : int, optional
        Minimum length of the annealing part of the primer.

    maxlength : int, optional
        Maximum length (including tail) for designed primers.

    fp, rp : SeqRecord, optional
        optional Biopython SeqRecord objects containing one primer each.

    fp_tail, rp_tail : string, optional
        optional tails to be added to the forwars or reverse primers.

    target_tm : float, optional
        target tm for the primers, set to 55°C by default.

    fprimerc : float, optional
        Concentration of forward primer in nM, set to 1000.0 nM by default.

    rprimerc : float, optional
        Concentration of reverse primer in nM, set to 1000.0 nM by default.

    saltc  : float, optional
        Salt concentration (monovalet cations) :mod:`tmbresluc` set to 50.0 mM by default

    formula : function
        formula used for tm calculation
        this is the name of a function.
        built in options are:

        1. :func:`pydna.amplify.tmbresluc` (default)
        2. :func:`pydna.amplify.basictm`
        3. :func:`pydna.amplify.tmstaluc98`
        4. :func:`pydna.amplify.tmbreslauer86`

        These functions are imported from the :mod:`pydna.amplify` module, but can be
        substituted for some other custom made function.

    Returns
    -------
    fp, rp : tuple
        fp is a :mod:Bio.SeqRecord object describing the forward primer
        rp is a :mod:Bio.SeqRecord object describing the reverse primer



    Examples
    --------

    >>> import pydna
    >>> t=pydna.Dseqrecord("atgactgctaacccttccttggtgttgaacaagatcgacgacatttcgttcgaaacttacgatg")
    >>> t
    Dseqrecord(-64)
    >>> pf,pr = pydna.cloning_primers(t)
    >>> pf
    fw64 17-mer:5'atgactgctaacccttc-3'
    >>> pr
    rv64 17-mer:5'catcgtaagtttcgaac-3'
    >>> pcr_prod = pydna.pcr(pf, pr, t)
    >>> pcr_prod
    Amplicon(64)
    >>>
    >>> print(pcr_prod.figure())
    5atgactgctaacccttc...gttcgaaacttacgatg3
                         ||||||||||||||||| tm 49.0 (dbd) 52.9
                        3caagctttgaatgctac5
    5atgactgctaacccttc3
     ||||||||||||||||| tm 51.6 (dbd) 54.0
    3tactgacgattgggaag...caagctttgaatgctac5
    >>> pf,pr = pydna.cloning_primers(t, fp_tail="GGATCC", rp_tail="GAATTC")
    >>> pf
    fw64 23-mer:5'GGATCCatgactgctaacccttc-3'
    >>> pr
    rv64 23-mer:5'GAATTCcatcgtaagtttcgaac-3'
    >>> pcr_prod = pydna.pcr(pf, pr, t)
    >>> print(pcr_prod.figure())
          5atgactgctaacccttc...gttcgaaacttacgatg3
                               ||||||||||||||||| tm 49.0 (dbd) 52.9
                              3caagctttgaatgctacCTTAAG5
    5GGATCCatgactgctaacccttc3
           ||||||||||||||||| tm 51.6 (dbd) 54.0
          3tactgacgattgggaag...caagctttgaatgctac5
    >>> print(pcr_prod.seq)
    GGATCCatgactgctaacccttccttggtgttgaacaagatcgacgacatttcgttcgaaacttacgatgGAATTC
    >>>
    >>> from Bio.Seq import Seq
    >>> from Bio.SeqRecord import SeqRecord
    >>> pf = SeqRecord(Seq("atgactgctaacccttccttggtgttg"))
    >>> pf,pr = pydna.cloning_primers(t, fp = pf, fp_tail="GGATCC", rp_tail="GAATTC")
    >>> pf
    SeqRecord(seq=Seq('GGATCCatgactgctaacccttccttggtgttg', Alphabet()), id='fw64', name='fw64', description='fw64 id?', dbxrefs=[])
    >>> pr
    rv64 34-mer:5'GAATTCcatcgtaagtttcgaacgaaatgtcgtc-3'
    >>> ampl = pydna.pcr(pf,pr,t)
    >>> print(ampl.figure())
          5atgactgctaacccttccttggtgttg...gacgacatttcgttcgaaacttacgatg3
                                         |||||||||||||||||||||||||||| tm 61.7 (dbd) 72.2
                                        3ctgctgtaaagcaagctttgaatgctacCTTAAG5
    5GGATCCatgactgctaacccttccttggtgttg3
           ||||||||||||||||||||||||||| tm 63.7 (dbd) 72.3
          3tactgacgattgggaaggaaccacaac...ctgctgtaaagcaagctttgaatgctac5
    >>>


    '''

    if fp and not rp:
        fp = _Primer(_Seq(fp_tail, _IUPACAmbiguousDNA())) + fp
        p  = _Anneal([fp], template).fwd_primers.pop()
        fp = _Primer(p.footprint)
        fp_tail = _Primer(p.tail)
        rp = _Primer(_Seq(str(template[-(maxlength*3-len(rp_tail)):].reverse_complement().seq), _IUPACAmbiguousDNA()))
        target_tm = formula(str(fp.seq).upper(), primerc=fprimerc, saltc=saltc)
    elif not fp and rp:
        rp = _Primer(_Seq(rp_tail, _IUPACAmbiguousDNA())) + rp
        p =  _Anneal([rp], template).rev_primers.pop()
        rp = _Primer(p.footprint)
        rp_tail = _Primer(p.tail)
        fp = _Primer(_Seq(str(template[:maxlength*3-len(fp_tail)].seq), _IUPACAmbiguousDNA()))
        target_tm = formula(str(rp.seq).upper(), primerc=rprimerc, saltc=saltc)
    elif not fp and not rp:
        fp = _Primer(_Seq(str(template[:maxlength*3-len(fp_tail)].seq), _IUPACAmbiguousDNA()))
        rp = _Primer(_Seq(str(template[-maxlength*3+len(rp_tail):].reverse_complement().seq), _IUPACAmbiguousDNA()))
    else:
        raise Exception("Specify maximum one of the two primers, not both.")

    fp.concentration = fprimerc
    rp.concentration = rprimerc
    
    lowtm, hightm = sorted( [( formula(str(fp.seq), fprimerc, saltc), fp, "f" ),
                             ( formula(str(rp.seq), rprimerc, saltc), rp, "r" ) ] , key=_itemgetter(0))
                          
    while lowtm[0] > target_tm and len(lowtm[1])>minlength:
        shorter = lowtm[1][:-1]
        tm      = formula(str(shorter.seq).upper(), primerc=fprimerc, saltc=saltc)
        lowtm   = (tm, shorter, lowtm[2])

    while hightm[0] > lowtm[0] + 2.0 and len(hightm[1])>minlength:
        shorter = hightm[1][:-1]
        tm = formula(str(shorter.seq).upper(), primerc = rprimerc, saltc = saltc)
        hightm = (tm, shorter, hightm[2])

    fp, rp = sorted((lowtm, hightm), key=_itemgetter(2))

    fp = fp_tail + fp[1]
    rp = rp_tail + rp[1]

    #fp.description = "fw{}".format(len(template))
    #rp.description = "rv{}".format(len(template))

    #fp.name = "fw{}".format(len(template))[:15]
    #rp.name = "rv{}".format(len(template))[:15]

    fp.description = "fw{}".format(len(template))+' '+template.accession
    rp.description = "rv{}".format(len(template))+' '+template.accession

    fp.id = "fw{}".format(len(template))
    rp.id = "rv{}".format(len(template))

    fp.name = fp.id
    rp.name = rp.id

    if fp.seq.alphabet == _Alphabet():
        fp.seq.alphabet = _IUPACAmbiguousDNA()
    if rp.seq.alphabet == _Alphabet():
        rp.seq.alphabet = _IUPACAmbiguousDNA()

    return fp, rp

def integration_primers( up,
                         cas,
                         dn,
                         uplink     = _Dseqrecord(''),
                         dnlink     = _Dseqrecord(''),
                         minlength  = 16,
                         maxlength  = 80,
                         min_olap   = 50,
                         target_tm  = 55.0,
                         fprimerc   = 1000.0,
                         rprimerc   = 1000.0,
                         saltc      = 50.0,
                         formula    = _tmbresluc):

    fp_tail = str(up[-min_olap:].seq) + str(uplink.seq)
    rp_tail = str(dn[:min_olap].rc().seq) + str(dnlink.rc().seq)

    #maxlength  = minlength + max(len(fp_tail), len(rp_tail))

    return cloning_primers( cas,
                            minlength=minlength,
                            maxlength=maxlength,
                            fp_tail=fp_tail,
                            rp_tail=rp_tail,
                            target_tm=target_tm,
                            fprimerc=fprimerc,
                            rprimerc=rprimerc,
                            saltc=saltc,
                            formula = formula)


def assembly_primers(templates,
                     circular   = False,
                     vector     = None,
                     maxlink    = 40,
                     minlength  = 16,
                     maxlength  = 50,
                     min_olap   = 35,
                     target_tm  = 55.0,
                     fprimerc   = 1000.0,
                     rprimerc   = 1000.0,
                     saltc      = 50.0,
                     formula    = _tmbresluc):


    '''This function return primer pairs that are useful for fusion of DNA sequences given in template.
    Given two sequences that we wish to fuse (a and b) to form fragment c.

    ::

       _________ a _________           __________ b ________
      /                     \\         /                     \\
      agcctatcatcttggtctctgca   <-->  TTTATATCGCATGACTCTTCTTT
      |||||||||||||||||||||||         |||||||||||||||||||||||
      tcggatagtagaaccagagacgt   <-->  AAATATAGCGTACTGAGAAGAAA


           agcctatcatcttggtctctgcaTTTATATCGCATGACTCTTCTTT
           ||||||||||||||||||||||||||||||||||||||||||||||
           tcggatagtagaaccagagacgtAAATATAGCGTACTGAGAAGAAA
           \\___________________ c ______________________/


    We can design tailed primers to fuse a and b by fusion PCR, Gibson assembly or
    in-vivo homologous recombination. The basic requirements for the primers for
    the three techniques are the same.


    Design tailed primers incorporating a part of the next or previous fragment to be assembled.

    ::


      agcctatcatcttggtctctgca
      |||||||||||||||||||||||
                      gagacgtAAATATA

      |||||||||||||||||||||||
      tcggatagtagaaccagagacgt


                             TTTATATCGCATGACTCTTCTTT
                             |||||||||||||||||||||||

                      ctctgcaTTTATAT
                             |||||||||||||||||||||||
                             AAATATAGCGTACTGAGAAGAAA

    PCR products with flanking sequences are formed in the PCR process.

    ::

      agcctatcatcttggtctctgcaTTTATAT
      ||||||||||||||||||||||||||||||
      tcggatagtagaaccagagacgtAAATATA
                      \\____________/

                         identical
                         sequences
                       ____________
                      /            \\
                      ctctgcaTTTATATCGCATGACTCTTCTTT
                      ||||||||||||||||||||||||||||||
                      gagacgtAAATATAGCGTACTGAGAAGAAA

    The fragments can be fused by any of the techniques mentioned earlier.

    ::

      agcctatcatcttggtctctgcaTTTATATCGCATGACTCTTCTTT
      ||||||||||||||||||||||||||||||||||||||||||||||
      tcggatagtagaaccagagacgtAAATATAGCGTACTGAGAAGAAA




    Parameters
    ----------

    templates : list of Dseqrecord
        list Dseqrecord object for which fusion primers should be constructed.

    minlength : int, optional
        Minimum length of the annealing part of the primer.

    maxlength : int, optional
        Maximum length (including tail) for designed primers.

    tot_length : int, optional
        Maximum total length of a the primers

    target_tm : float, optional
        target tm for the primers

    primerc : float, optional
        Concentration of each primer in nM, set to 1000.0 nM by default

    saltc  : float, optional
        Salt concentration (monovalet cations) :mod:`tmbresluc` set to 50.0 mM by default

    formula : function
        formula used for tm calculation
        this is the name of a function.
        built in options are:

        1. :func:`pydna.amplify.tmbresluc` (default)
        2. :func:`pydna.amplify.basictm`
        3. :func:`pydna.amplify.tmstaluc98`
        4. :func:`pydna.amplify.tmbreslauer86`

        These functions are imported from the :mod:`pydna.amplify` module, but can be
        substituted for some other custom made function.

    Returns
    -------
    primer_pairs : list of tuples of :mod:`Bio.Seqrecord` objects

        ::

          [(forward_primer_1, reverse_primer_1),
           (forward_primer_2, reverse_primer_2), ...]


    Examples
    --------

    >>> import pydna
    >>> a=pydna.Dseqrecord("atgactgctaacccttccttggtgttgaacaagatcgacgacatttcgttcgaaacttacgatg")
    >>> b=pydna.Dseqrecord("ccaaacccaccaggtaccttatgtaagtacttcaagtcgccagaagacttcttggtcaagttgcc")
    >>> c=pydna.Dseqrecord("tgtactggtgctgaaccttgtatcaagttgggtgttgacgccattgccccaggtggtcgtttcgtt")
    >>> primer_pairs = pydna.assembly_primers([a,b,c], circular = True)
    >>> p=[]
    >>> for t, (f,r) in zip([a,b,c], primer_pairs): p.append(pydna.pcr(f,r,t))
    >>> p
    [Amplicon(100), Amplicon(101), Amplicon(102)]
    >>> assemblyobj = pydna.Assembly(p)
    >>> assemblyobj
    Assembly:
    Sequences........................: [100] [101] [102]
    Sequences with shared homologies.: [100] [101] [102]
    Homology limit (bp)..............: 25
    Number of overlaps...............: 3
    Nodes in graph(incl. 5' & 3')....: 5
    Only terminal overlaps...........: No
    Circular products................: [195]
    Linear products..................: [231] [231] [231] [167] [166] [165] [36] [36] [36]
    >>> assemblyobj.linear_products
    [Contig(-231), Contig(-231), Contig(-231), Contig(-167), Contig(-166), Contig(-165), Contig(-36), Contig(-36), Contig(-36)]
    >>> assemblyobj.circular_products[0].cseguid()
    'V3Mi8zilejgyoH833UbjJOtDMbc'
    >>> (a+b+c).looped().cseguid()
    'V3Mi8zilejgyoH833UbjJOtDMbc'
    >>> print(assemblyobj.circular_products[0].small_fig())
     -|100bp_PCR_prod|36
    |                 \\/
    |                 /\\
    |                 36|101bp_PCR_prod|36
    |                                   \\/
    |                                   /\\
    |                                   36|102bp_PCR_prod|36
    |                                                     \\/
    |                                                     /\\
    |                                                     36-
    |                                                        |
     --------------------------------------------------------
    >>>





    '''

    if vector:
        circular = False

    if not hasattr(templates, '__iter__'):
        raise Exception("first argument has to be an iterable")

    tail_length =  int(_math.ceil(float(min_olap)/2))

    if circular:
        templates = tuple(templates) + (templates[0],)

    linkers = []
    newtemplates=[]

    for t in templates:
        if len(t)<=maxlink:
            linker = t
        else:
            linker= _Dseqrecord('')
            newtemplates.append(t)
        linkers.append(linker)

    newtails = []
    linkers = linkers[1:]+[linkers[0]]

    for t,n,l in zip(newtemplates, newtemplates[1:], linkers):
        length = tail_length - len(l)//2
        newtails.extend( (str(n[:length].rc().seq)+str(l.rc().seq),
                          str(t.seq[-length:])+str(l.seq) ))

    if not circular:
        newtails = [""] + newtails + [""]
    else:
        newtails = [newtails[-1]] + newtails[:-1]

    tails =  list(zip(newtails[::2], newtails[1::2]))

    primer_pairs = []

    for template, (fp_tail, rp_tail) in zip(newtemplates, tails):

        fp, rp = cloning_primers(   template,
                                    minlength  = minlength,
                                    maxlength  = maxlength,
                                    fp_tail    = fp_tail,
                                    rp_tail    = rp_tail,
                                    target_tm  = target_tm,
                                    fprimerc   = fprimerc,
                                    rprimerc   = rprimerc,
                                    saltc      = saltc,
                                    formula    = formula)

        #fp = _Primer(_Seq(fp_tail, IUPACAmbiguousDNA())) + fp
        #rp = _Primer(_Seq(fp_tail, IUPACAmbiguousDNA())) + rp

        primer_pairs.append((fp, rp))

    if vector:
        fake_cas = templates[0]+templates[-1]
        pa, pb   = integration_primers( vector,
                                        fake_cas,
                                        vector,
                                        min_olap=min_olap)

        primer_pairs[0]  = (pa, primer_pairs[0][1])
        primer_pairs[-1] = (primer_pairs[-1][0], pb)

    return primer_pairs


if __name__=="__main__":
    import os as _os
    cache = _os.getenv("pydna_cache", "nocache")
    _os.environ["pydna_cache"]="nocache"
    import doctest
    doctest.testmod(verbose=True, optionflags=doctest.ELLIPSIS)
    _os.environ["pydna_cache"]=cache

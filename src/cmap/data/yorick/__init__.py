"""These palettes are from the Yorick scientific visalisation package,.

Yorik is an evolution of the GIST package, both by David H. Munro.

https://github.com/LLNL/yorick
https://yorick.sourceforge.net/index.php

Copyright:

  Copyright (c) 1996.  The Regents of the University of California.
                         All rights reserved.

Permission to use, copy, modify, and distribute this software for any
purpose without fee is hereby granted, provided that this entire
notice is included in all copies of any software which is or includes
a copy or modification of this software and in all copies of the
supporting documentation for such software.

This work was produced at the University of California, Lawrence
Livermore National Laboratory under contract no. W-7405-ENG-48 between
the U.S. Department of Energy and The Regents of the University of
California for the operation of UC LLNL.


                              DISCLAIMER

This software was prepared as an account of work sponsored by an
agency of the United States Government.  Neither the United States
Government nor the University of California nor any of their
employees, makes any warranty, express or implied, or assumes any
liability or responsibility for the accuracy, completeness, or
usefulness of any information, apparatus, product, or process
disclosed, or represents that its use would not infringe
privately-owned rights.  Reference herein to any specific commercial
products, process, or service by trade name, trademark, manufacturer,
or otherwise, does not necessarily constitute or imply its
endorsement, recommendation, or favoring by the United States
Government or the University of California.  The views and opinions of
authors expressed herein do not necessarily state or reflect those of
the United States Government or the University of California, and
shall not be used for advertising or product endorsement purposes.


                                AUTHOR

David H. Munro wrote Yorick and Gist.  Berkeley Yacc (byacc) generated
the Yorick parser.  The routines in Math are from LAPACK and FFTPACK;
MathC contains C translations by David H. Munro.  The algorithms for
Yorick's random number generator and several special functions in
Yorick/include were taken from Numerical Recipes by Press, et. al.,
although the Yorick implementations are unrelated to those in
Numerical Recipes.  A small amount of code in Gist was adapted from
the X11R4 release, copyright M.I.T. -- the complete copyright notice
may be found in the (unused) file Gist/host.c.
"""

import numpy as np

# https://github.com/LLNL/yorick/blob/fda4a1ed1e2441e30de88e01b251b822f3604b1f/g/earth.gp
earth = [
    (0.0, (0.0, 0.0, 0.0, 1.0)),
    (0.0039, (0.0025990793201133146, 0.0, 0.1684, 1.0)),
    (0.0078, (0.005198158640226629, 0.0, 0.2212, 1.0)),
    (0.0275, (0.01832684135977337, 0.0, 0.4329, 1.0)),
    (0.0314, (0.020925920679886686, 0.008970473876063177, 0.4549, 1.0)),
    (0.1098, (0.07317407932011331, 0.1893, 0.4691119521912351, 1.0)),
    (0.1647, (0.10976111898016998, 0.3035, 0.47906394422310755, 1.0)),
    (0.2078, (0.1384842776203966, 0.3841, 0.4868768924302789, 1.0)),
    (0.2824, (0.1882, 0.502, 0.5004, 1.0)),
    (0.4588, (0.2714, 0.6035479933110368, 0.28447032013022244, 1.0)),
    (0.4667, (0.28896042128603106, 0.6080957775919733, 0.2748, 1.0)),
    (0.5216, (0.41099423503325927, 0.6397, 0.30680165816326527, 1.0)),
    (0.5451, (0.46323093126385806, 0.650011224489796, 0.3205, 1.0)),
    (0.549, (0.4719, 0.6517224489795919, 0.3217326086956522, 1.0)),
    (0.698, (0.7176, 0.7171, 0.36882458193979933, 1.0)),
    (0.7843, (0.753669955654102, 0.6425681818181819, 0.3961, 1.0)),
    (0.7882, (0.7553, 0.6392, 0.4056546448087432, 1.0)),
    (0.7922, (0.7597740321057601, 0.6413, 0.41545428051001826, 1.0)),
    (0.8, (0.7684983947119924, 0.6447, 0.4345635701275047, 1.0)),
    (0.8078, (0.7772227573182247, 0.6481, 0.45367285974499083, 1.0)),
    (0.8157, (0.786058970727101, 0.6549, 0.4730271402550091, 1.0)),
    (0.8667, (0.8431028800755429, 0.6991, 0.597972495446266, 1.0)),
    (0.8745, (0.8518272426817752, 0.7103, 0.6170817850637524, 1.0)),
    (0.8824, (0.8606634560906514, 0.7216, 0.6364360655737704, 1.0)),
    (0.8902, (0.8693878186968838, 0.7323, 0.6555453551912569, 1.0)),
    (0.8941, (0.87375, 0.7376499999999999, 0.6651, 1.0)),
    (0.898, (0.8781121813031161, 0.743, 0.6768552407932013, 1.0)),
    (0.9412, (0.9264317280453258, 0.8275, 0.8070671388101984, 1.0)),
    (0.9569, (0.9439923040604343, 0.8635, 0.8543895184135977, 1.0)),
    (0.9647, (0.9527166666666667, 0.8816, 0.8779, 1.0)),
    (0.9961, (0.9878378186968838, 0.9733, 0.9725447592067988, 1.0)),
    (1.0, (0.9922, 0.9843, 0.9843, 1.0)),
]

# https://github.com/LLNL/yorick/blob/fda4a1ed1e2441e30de88e01b251b822f3604b1f/g/ncar.gp

ncar = [
    (0.0, (0.0, 0.0, 0.502, 1.0)),
    (0.051, (0.0, 0.3722, 0.0222, 1.0)),
    (0.1059, (0.0, 0.0, 0.9351459183673468, 1.0)),
    (0.1098, (0.0, 0.05507411764705881, 1.0, 1.0)),
    (0.1569, (0.0, 0.7202, 1.0, 1.0)),
    (0.1608, (0.0, 0.7537, 1.0, 1.0)),
    (0.1647, (0.0, 0.7752, 1.0, 1.0)),
    (0.2039, (0.0, 0.9479874509803922, 1.0, 1.0)),
    (0.2157, (0.0, 1.0, 0.9226377551020408, 1.0)),
    (0.2588, (0.0, 0.9804, 0.6400688775510206, 1.0)),
    (0.2627, (0.0, 0.9804, 0.6145, 1.0)),
    (0.2706, (0.0, 0.9804, 0.5320797962648556, 1.0)),
    (0.3098, (0.0, 0.9967472340425532, 0.12310865874363303, 1.0)),
    (0.3176, (0.04967368421052617, 1.0, 0.041731748726655415, 1.0)),
    (0.3216, (0.07514736842105252, 0.9849490196078431, 0.0, 1.0)),
    (0.3686, (0.3744631578947368, 0.8081, 0.0, 1.0)),
    (0.3725, (0.3993, 0.8208064516129033, 0.0, 1.0)),
    (0.4157, (0.4848529411764706, 0.9615548387096775, 0.0, 1.0)),
    (0.4235, (0.5003, 0.9869677419354839, 0.031067346938775425, 1.0)),
    (0.4275, (0.5185040072859745, 1.0, 0.04699931972789109, 1.0)),
    (0.4745, (0.7324010928961748, 1.0, 0.2342, 1.0)),
    (0.5216, (0.9467532786885244, 1.0, 0.04660102040816341, 1.0)),
    (0.5333, (1.0, 0.9711442622950819, 0.0, 1.0)),
    (0.5804, (1.0, 0.8549814207650271, 0.0, 1.0)),
    (0.6314, (1.0, 0.7292, 0.0549, 1.0)),
    (0.6863, (1.0, 0.2796, 0.003641326530612256, 1.0)),
    (0.6902, (1.0, 0.2610551020408163, 0.0, 1.0)),
    (0.7373, (1.0, 0.0370897959183675, 0.0, 1.0)),
    (0.7451, (1.0, 0.0, 0.13835409836065612, 1.0)),
    (0.7922, (1.0, 0.0, 0.9738, 1.0)),
    (0.8, (0.9462666666666664, 0.026863261296660248, 1.0, 1.0)),
    (0.8431, (0.6493555555555557, 0.1753, 1.0, 1.0)),
    (0.8471, (0.6218, 0.1989575591985428, 0.9951985428051002, 1.0)),
    (0.898, (0.9235, 0.5, 0.9341, 1.0)),
    (1.0, (0.9961, 0.9725, 0.9961, 1.0)),
]

# https://github.com/LLNL/yorick/blob/fda4a1ed1e2441e30de88e01b251b822f3604b1f/g/stern.gp
stern = [
    (0.0, (0.0, 0.0, 0.0, 1.0)),
    (0.0547, (1.0, 0.0547, 0.1094, 1.0)),
    (0.25, (0.025, 0.25, 0.5, 1.0)),
    (0.5, (0.34991332177623685, 0.5, 1.0, 1.0)),
    (0.735, (0.6554540605414054, 0.735, 0.0, 1.0)),
    (1.0, (1.0, 1.0, 1.0, 1.0)),
]

# https://github.com/LLNL/yorick/blob/fda4a1ed1e2441e30de88e01b251b822f3604b1f/g/yarg.gp
yarg = [[255, 255, 255], [0, 0, 0]]


def heat(x: np.ndarray) -> np.ndarray:
    """Heat colormap function."""
    return np.stack([1.5 * x, 2 * x - 1, 4 * x - 3], axis=-1)


# https://github.com/LLNL/yorick/blob/fda4a1ed1e2441e30de88e01b251b822f3604b1f/g/rainbow.gp
rainbow = [
    (0.000, (1.00, 0.00, 0.16)),
    (0.030, (1.00, 0.00, 0.00)),
    (0.215, (1.00, 1.00, 0.00)),
    (0.400, (0.00, 1.00, 0.00)),
    (0.586, (0.00, 1.00, 1.00)),
    (0.770, (0.00, 0.00, 1.00)),
    (0.954, (1.00, 0.00, 1.00)),
    (1.000, (1.00, 0.00, 0.75)),
]

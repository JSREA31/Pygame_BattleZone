import numpy as np

def translationMatrix(coords):
     return np.array([[1,0.0,0.0,0.0],
                    [0.0,1,0.0,0.0],
                    [0.0,0.0,1,0.0],
                    [coords[0],coords[1],coords[2],1]])


def rotateXMatrix(radians):
    """ Return matrix for rotating about the x-axis by 'radians' radians """

    c = np.cos(radians)
    s = np.sin(radians)
    return np.array([[1, 0.0, 0.0, 0.0],
                        [0.0, c,s, 0.0],
                        [0.0, -s, c, 0.0],
                        [0.0, 0.0, 0.0, 1]])


def rotateYMatrix(radians):
    """ Return matrix for rotating about the y-axis by 'radians' radians """

    c = np.cos(radians)
    s = np.sin(radians)
    return np.array([[ c, 0.0, -s, 0.0],
                        [ 0.0, 1, 0.0, 0.0],
                        [s, 0.0, c, 0.0],
                        [ 0.0, 0.0, 0.0, 1]])


def rotateZMatrix(radians):
    """ Return matrix for rotating about the z-axis by 'radians' radians """

    c = np.cos(radians)
    s = np.sin(radians)
    return np.array([[c,s, 0.0, 0.0],
                        [-s, c, 0.0, 0.0],
                        [0.0, 0.0, 1, 0.0],
                        [0.0, 0.0, 0.0, 1]])


def scaleMatrix(scale):
    """ Return matrix for scaling equally along all axes centred on the point (cx,cy,cz). """
    return np.array([[scale[0], 0.0,  0.0,  0.0],
                        [0.0,  scale[1], 0.0,  0.0],
                        [0.0,  0.0,  scale[2], 0.0],
                        [0.0,  0.0,  0.0,  1]])


def perspectiveMatrix(sx=0.0, sy=0.0, sz=0.0):
    """ Return matrix for perspetive scaling """

    return np.array([[sx, 0.0,  0.0,  0.0],
                        [0.0,  sy, 0.0,  0.0],
                        [0.0,  0.0,  sz, 0.0],
                        [0.0,  0.0,  0.0,  0.0]])

def perspectiveMatrix2(a=0.0, b=0.0, c=0.0, q=0.0):
    """ Return matrix for perspetive scaling """

    return np.array([[q, 0.0,  0.0,  0.0],
                        [0.0,  q, 0.0,  0.0],
                        [0.0,  0.0,  b, c],
                        [0.0,  0.0,  -1.0,  0.0]])
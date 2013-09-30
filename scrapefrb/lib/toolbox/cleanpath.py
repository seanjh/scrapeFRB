__author__ = 'sherman'
# paths.py
# by Sean J. Herman

import os
import logging


def path_to_list(p):
    '''Transforms a path string into a list of directory strings, in order.
    Index 0 includes root/mount (e.g., 'C:\\' or '/').

        >>> path_str = 'C:\\Users\\johndoe\\Documents\\'
        >>> path_to_list(path_str)
        ['C:\\', 'Users', 'johndoe', 'Documents', '']

        >>> path_str = '/home/seanh/Documents/'
        >>> path_to_list(path_str)
        ['/', 'home', 'seanh', 'Documents', '']
    '''
    path_list = []
    head, tail = os.path.split(p)
    while not os.path.ismount(head):
        path_list.append(tail)
        head, tail = os.path.split(head)
    # Add the last pieces.
    path_list.append(tail)
    path_list.append(head)
    path_list.reverse()
    if not path_list[-1]:
        path_list.pop(-1)
    return path_list


def path_exists(p):
    try:
        if os.path.exists(p):
            return True
        else:
            return False
    except TypeError:
        pathstring = os.path.join(*p)
        if os.path.exists(pathstring):
            return True
        else:
            return False


def path_valid(p):
    validpath = False
    try:
        p.append(p.pop())
        os.path.exists(os.path.join(*p))
        validpath = True
    except AttributeError:
        try:
            os.path.exists(p)
            validpath = True
        except TypeError:
            logging.ERROR("Invalid path value!")
    except TypeError:
        logging.ERROR("Invalid path value!")
    return validpath


def path_is_list(p):
    try:
        p.append(p.pop())
        return True
    except AttributeError:
        logging.ERROR("Invalid path value!")
    except ValueError:
        pass
    return False


def check_path_make(p):
    """Checks for the existence of some directory. The directory is created
    if it does not exist already. Accepts strings or lists as input.
    """
    if path_valid(p):
        if not path_exists(p):
            if path_is_list(p):
                p = os.path.join(*p)
                logging.info("%s does not exist. Creating the new directory." % p)
                os.mkdir(p)
            else:
                logging.info("%s does not exist. Creating the new directory." % p)
                os.mkdir(p)
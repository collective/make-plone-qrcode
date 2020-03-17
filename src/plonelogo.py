# -*- coding: utf-8 -*- הצü

import pyqrcode
from lxml import etree
from lxml.builder import ElementMaker
from StringIO import StringIO
from os.path import splitext

from thebops.optparse import OptionParser, OptionGroup
from thebops.opo import (add_version_option, add_help_option,
        add_verbosity_options,
        )
from thebops.errors import err, fatal, check_errors, info
from thebops.colours import add_colour_option, SVG_COLOURS

__author__ = 'Tobias Herp <tobias.herp@visaplan.com>'
__version__ = 'make-plone-qrcode v0.1'


SVG_COLOURS['plone'] = (0, 157, 220)

def _(s, *args, **kwargs):  # i18n dummy
    return s


def channel_value(num):
    if isinstance(num, float):
        if num > 1.0:
            raise ValueError('%(num)r: numbers above 1.0 are expected '
                    'to be integers!' % locals())
        elif num < 0:
            raise ValueError('%(num)r: non-negative value expected!'
                    % locals())
        else:
            return str(num)
    elif not isinstance(num, int):
        raise ValueError('%(num)r: int or float value expected!'
                         % locals())
    elif 0 <= num:
        return str(min(num, 255))
    else:
        raise ValueError('%(num)r: values < 0 are forbidden!'
                         % locals())

def untuple_colour(val):
    """
    >>> untuple_colour((0, 0, 0))
    '#000000'
    >>> untuple_colour((1, 2, 3, 127))
    'rgba(1,2,3,127)'
    """
    if isinstance(val, tuple):
        if val[4:]:
            raise ValueError('Tuple too long!')
        elif val[3:]:
            return ','.join(map(channel_value, val)).join(('rgba(', ')'))
        return '#'+''.join(['%(num)02x' % locals()
                            for num in val])
    return val


def make_parser():
    p = OptionParser(description=_('Create QR codes with the Plone logo injected'),
            add_help_option=False,
            usage='%prog [options] {string} {filename}')
    g = OptionGroup(p, 'QR Code creation')
    g.add_option('--title',
                 type='string',
                 help=_('A title for the QR code; empty '
                 'by default.'
                 ' This is not a visible caption text,'
                 ' and it is not guaranteed that browsers honour it in any way!'
                 ))
    g.add_option('--url',
                 type='string',
                 help=_('A URL to be encoded; if no protocol is given,'
                 ' "https://" is prepended by default.'
                 ' Can be alternatively specified'
                 ' as the 1st positional argument.'
                 ' If a --title was given, the --url defaults to that title'
                 ' preprended by an "https://" protocol prefix.'
                 ))
    g.add_option('--scale',
                 type='float',
                 metavar='N',
                 default=4,
                 help=_('The scale to be used, default: %default, which will '
                 'cause the "modules" to span %default screen pixels.'
                 ))
    g.add_option('--quiet-zone',
                 type='int',
                 default=4,
                 metavar='N',
                 help=_('By default, the code is surrounded by a "quiet zone"'
                 ' of %default module widths, as requested by the standard;'
                 ' this can be overridden'
                 ' e.g. if the margin is created otherwise.'
                 ))
    # doesn't emit string values yet; we'll need to convert ourselves:
    add_colour_option(g, '--module-color', '--module-colour',
                 default='black',
                 help=_('A valid XML color specification, or "plone", '
                 'which will be translated to "#009ddc", the colour of the Plone '
                 'logo; default: %default.'
                 ))
    add_colour_option(g, '--background',
                 alpha=True,
                 opacity=1.0,
                 help=_('Optional; if nothing is specified, no background is '
                 'created, i.e. the code part will be transparent. '
                 'This colour will be used for the logo as well. '
                 'You may use any HTML or SVG colour name '
                 'or any numeric RGB-based specification including rgba(...); '
                 'however, for the logo we need full opacity (1.0), so the '
                 'logo background is opaque and white by default, and any '
                 'alpha channel value will only be used for the QR code part.'
                 ))
    p.add_option_group(g)

    g = OptionGroup(p, 'Logo injection')
    g.add_option('--logo-size',
                 type='float',
                 default=32,
                 metavar='NN.N',
                 help=_('The size of the Plone logo in percent; default: %default.'
                 ' QR codes contain enough redundancy to cope with up to 30% of '
                 'the data modules covered; you may try higher values, but '
                 'you\'ll need to check the result for scanability yourself.'
                 ))
    add_colour_option(g, '--logo-color', '--logo-colour',
                 metavar='#009ddc',
                 help=_('A valid XML color specification, or "plone", '
                 'which will be translated to "#009ddc", the color of the Plone '
                 'logo.'
                 ' Defaults to the module color.'
                 ))
    g.add_option('--extra-space',
                 type='float',
                 dest='space_percent',
                 default=3,
                 metavar='N.N',
                 help=_('Extra space around the Plone logo, '
                 'in percent relative to the total size'
                 ' (so the resulting percentage is the sum of --logo-size'
                 ' and --extra-space)'
                 '; default: %default.'
                 ))
    p.add_option_group(g)

    g = OptionGroup(p, 'File options')
    g.add_option('--name',
                 type='string',
                 dest='filename',
                 metavar='plone.svg',
                 help=_('The name of the file to write;'
                 ' can be alternatively specified'
                 ' as the 2nd positional argument.'
                 ' Unless already present, a ".svg" extension is appended.'
                 ))
    p.add_option_group(g)

    g = OptionGroup(p, 'Everyday options')
    add_verbosity_options(g, default=1)
    add_version_option(g, version=__version__)
    add_help_option(g)
    p.add_option_group(g)
    return p


def s(num):
    if isinstance(num, int) or num.is_integer():
        return '%(num)d' % locals()
    return '%(num).3f' % locals()


def plone_logo_elements(total, **kwargs):
    """
    total -- the total size of the SVG (in screen pixels);
             all other arguments are taken from options
    """
    pop = kwargs.pop
    logo_color = pop('logo_color')
    percent = pop('logo_size') / 100.0
    space_percent = pop('space_percent', 3.0) / 100.0
    background = pop('background', 'white')
    if kwargs:
        keys = list(kwargs.keys())
        raise TypeError('Unsupported keyword arguments %(keys)s!'
                        % locals())
    logo_height = logo_width = total * percent
    if space_percent > 0:
        space_radius = total * (percent + space_percent) / 2.0
    logo_radius = logo_height / 2.0
    logo_strike = logo_height / 10.0
    # first we calculate simple "inner" values
    vertical_tangent_x = logo_height * 6 / 11
    small_radius = (71.0 / 330 / 2  # from PNG studies
                    * logo_height)
    cx1 = cx2 = vertical_tangent_x - small_radius
    cx3 = vertical_tangent_x + small_radius

    upper_horizontal_tangent = (58.0 / 330  # from PNG studies
                                * logo_height)
    cy1 = upper_horizontal_tangent + small_radius
    cy2 = logo_height - cy1

    offset = (total - logo_height) / 2
    # now add the offset
    cx1 += offset
    cx2 += offset
    cx3 += offset
    cy1 += offset
    cy2 += offset
    cy3 = the_middle = total / 2.0

    E = ElementMaker(namespace='http://www.w3.org/2000/svg')
    CIRCLE = E.circle
    # spacer:
    if space_percent > 0:
        yield CIRCLE(cx=s(the_middle), cy=s(the_middle),
                     r=s(space_radius), fill=background)
    # the ring:
    yield CIRCLE(cx=s(the_middle), cy=s(the_middle),
                 r=s(logo_radius), fill=logo_color)
    yield CIRCLE(cx=s(the_middle), cy=s(the_middle),
                 r=s(logo_radius-logo_strike), fill=background)
    # small disks:
    yield CIRCLE(cx=s(cx1), cy=s(cy1), r=s(small_radius), fill=logo_color)
    yield CIRCLE(cx=s(cx2), cy=s(cy2), r=s(small_radius), fill=logo_color)
    yield CIRCLE(cx=s(cx3), cy=s(cy3), r=s(small_radius), fill=logo_color)


def main():
    p = make_parser()
    o, a = p.parse_args()
    if o.url is not None:
        text = o.url
    elif o.title is not None:
        text = o.title
    else:
        try:
            text = a.pop(0)
        except IndexError:
            err('No text (usually a URL) given!')
            text = None

    filename = None
    if o.filename is not None:
        filename = o.filename
    else:
        try:
            filename = a.pop(0)
        except IndexError:
            err('No filename given!')
    if filename is not None:
        stem, ext = splitext(filename)
        if ext.lower() != '.svg':
            filename += '.svg'

    check_errors()

    if o.logo_color is None:
        o.logo_color = o.module_color

    io = StringIO()
    if not '://' in text:
        text = 'https://'+text
        if o.verbose:
            info('Encoding text '+text)

    code_o = pyqrcode.create(text)
    svg_kwargs = {}
    if o.title is not None:
        svg_kwargs['title'] = o.title
    if o.quiet_zone is not None:
        svg_kwargs['quiet_zone'] = o.quiet_zone
    if o.module_color is not None:
        svg_kwargs['module_color'] = untuple_colour(o.module_color)
    if o.background is not None:
        svg_kwargs['background'] = untuple_colour(o.background)
    if o.scale is not None:
        svg_kwargs['scale'] = o.scale


    logo_kwargs = {
            'logo_color': untuple_colour(o.logo_color),
            'logo_size':  o.logo_size,
            }
    if o.background is not None:
        logo_kwargs['background'] = untuple_colour(o.background[:3])

    code_o.svg(io, **svg_kwargs)
    io.seek(0)
    tree = etree.parse(io)
    total_width = None
    theroot = None
    for elem in tree.iter():
        if elem.tag == '{http://www.w3.org/2000/svg}svg':
            val = elem.attrib['width']
            try:
                total_width = int(val)
            except ValueError:
                tmp = float(val)
                total_width = int(tmp)
            theroot = elem
            break

    if total_width is None:
        fatal('No width information found in generated SVG file!')

    for e in plone_logo_elements(total_width, **logo_kwargs):
        theroot.append(e)

    with open(filename, 'wb') as f:
        f.write(etree.tostring(theroot))
        if o.verbose:
            info('%(filename)s written' % locals())

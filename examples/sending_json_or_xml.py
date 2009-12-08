import json # or ``import simplejson as json`` for < Python 2.6
import xml.etree.ElementTree as etree # or other ElementTree variants for < Python 2.5
from itty import *

@get('/json')
def send_json(request):
    return Response(json.dumps({'foo': 'bar', 'moof': 123}), content_type='application/json')

@get('/xml')
def send_xml(request):
    xml = etree.Element('doc')
    foo = etree.SubElement(xml, 'foo', value='bar')
    foo = etree.SubElement(xml, 'moof', value='123')
    return Response(etree.tostring(xml), content_type='application/xml')

run_itty()

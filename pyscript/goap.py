
# Edit the configuration below:

CONFIG = {
    'address': {
        'city': 'Your city',
        'street_name': 'Your street name',
        'house_number': 'Your house number'
    },
    # Below you can change the name and color of generated entities
    # The german IDs ('glas', 'rest', etc) are used in the API and can't be modified
    'entities':  {
        'glas': {
            'name': 'Szkło',
            'color': 'green'
        },
        'rest': {
            'name': 'Zmieszane',
            'color': 'gray'
        },
        'plastik': {
            'name': 'Plastik',
            'color': 'yellow'
        },
        'papier': {
            'name': 'Papier',
            'color': 'blue'
        },
        'bio': {
            'name': 'Bio',
            'color': 'brown'
        },
        'sperr': {
            'name': 'Gabaryty',
            'color': 'purple'
        }
    }
}




import asyncio
import aiohttp
from slugify import slugify
from bs4 import BeautifulSoup
from datetime import datetime

req_url = 'https://web.c-trace.de/zmgoappoznan-abfallkalender/kalendarzodpadow'
req_params = {
    'posted': 'yes',
    'ort': CONFIG['address']['city'],
    'strasse': CONFIG['address']['street_name'],
    'hausnr': CONFIG['address']['house_number']
}

def get_date(german_id, html_data):
    items = list(map(lambda x: datetime.strptime(x, '%d.%m.%Y').date(), filter(lambda x: len(x)==10, html_data.select('.plan.%s>ul' % german_id)[0].text.split())))
    return min([i for i in items if i >= datetime.now().date()], key=lambda x: abs(x - datetime.now().date()))

def set_state(german_id, date):
    entity_conf = CONFIG['entities'][german_id]
    entity_id = slugify(entity_conf['name'])
    diff = date-datetime.now().date()
    days = diff.days
    sta = 2
    if(days < 0):
        return
    if(days < 2):
        sta = days
    attrs = {
        'friendly_name': entity_conf['name'],
        'next_date': date.isoformat(),
        'days': days,
        'icon': 'mdi:trash-can',
        'icon_color': entity_conf['color']
    }
    state.set('sensor.goap_' + entity_id, value=sta, new_attributes=attrs)
    return
    
@time_trigger("startup")
@time_trigger("once(00:00:00)")
async def garbage_refresh():
    async with aiohttp.ClientSession() as session:
        async with session.get(req_url, params=req_params) as resp:
            if(resp.status != 200):
                log.error("GOAP Error, status code " + str(resp.status))
                return
            raw_html = resp.text()
    html_data = BeautifulSoup(raw_html, 'html.parser')

    for german_id in CONFIG['entities']:
        date = get_date(german_id, html_data)
        set_state(german_id, date)
import asyncio
from core import utils
from core.report.errors import ValueNotInRange
from typing import Any, List, Tuple


def parse_params(kwargs: dict, params: Tuple[dict, List]):
    new_args = kwargs.copy()
    if isinstance(params, dict):
        for key, value in params.items():
            new_args[key] = value
    else:
        new_args['params'] = params
    return new_args


async def parse_input(kwargs: dict, params: List[Any]):
    new_args = kwargs.copy()
    for param in params:
        if 'name' in param:
            if param['name'] in new_args and new_args[param['name']]:
                if 'range' in param:
                    value = new_args[param['name']] or ''
                    if value not in param['range']:
                        raise ValueNotInRange(param['name'], value, param['range'])
                elif 'value' in param:
                    value = param['value']
                    new_args[param['name']] = utils.format_string(value, '_ _', **kwargs) if isinstance(value, str) \
                        else value
            elif 'value' in param:
                value = param['value']
                new_args[param['name']] = utils.format_string(value, '_ _', **kwargs) if isinstance(value, str) \
                    else value
            elif 'default' in param:
                new_args[param['name']] = param['default']
        elif 'callback' in param:
            try:
                data: dict = await kwargs['server'].sendtoDCSSync({
                    "command": "getVariable", "name": param['callback']
                })
                if 'value' in data:
                    new_args[param['callback']] = data['value']
            except asyncio.TimeoutError:
                new_args[param['callback']] = None
    return new_args

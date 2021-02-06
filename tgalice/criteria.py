from .dialog import Context
from .dialog.names import REQUEST_TYPES


def is_morning_show_context(ctx: Context) -> bool:
    if not ctx.yandex or not ctx.yandex.request:
        return False
    r = ctx.yandex.request
    if r.type != REQUEST_TYPES.SHOW_PULL:
        return False
    return r.show_type == 'MORNING'

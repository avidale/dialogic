from .cascade import DialogTurn


def is_morning_show(turn: DialogTurn) -> bool:
    if not turn.ctx.yandex or not turn.ctx.yandex.request:
        return False
    r = turn.ctx.yandex.request
    if r.type != 'Show.Pull':
        return False
    return r.show_type == 'MORNING'

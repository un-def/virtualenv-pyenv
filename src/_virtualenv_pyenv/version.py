import operator
import re
from functools import partial
from typing import Any, Optional, Tuple


VERSION_REGEX = re.compile(
    r'(?P<base>\d(?:\.\d+){1,2})(?:(?P<pre>(?:a|b|rc)\d+)?|-(?P<dev>dev))')


class Readonly:

    def __set_name__(self, owner, name):
        self.private_name = f'_{name}'

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return getattr(instance, self.private_name)


class Cached:

    def __init__(self, func):
        self.func = func

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        res = instance.__dict__[self.name] = self.func(instance)
        return res


class Comparison:

    def __set_name__(self, owner, name):
        self.op = getattr(operator, name)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return partial(self._compare, instance)

    def _compare(self, left: 'Version', right: Any) -> bool:
        if not isinstance(right, Version):
            return NotImplemented
        return self.op(left._comparable, right._comparable)


class Version:

    def __init__(
        self,
        base: Tuple[int, ...],
        pre: Optional[Tuple[str, int]] = None,
        dev: bool = False,
    ) -> None:
        self._base = base
        self._pre = pre
        self._dev = dev

    base = Readonly()
    pre = Readonly()
    dev = Readonly()

    @Cached
    def _base_short(self) -> Tuple:
        base = self._base
        for offset in range(len(base) - 1, -1, -1):
            if base[offset]:
                return base[:offset + 1]
        return ()

    @Cached
    def _hash(self) -> int:
        return hash((self._base_short, self._pre, self._dev))

    @Cached
    def _comparable(
        self,
    ) -> Tuple[Tuple[int, ...], int, int, Optional[Tuple[str, int]]]:
        return (
            self._base_short,
            -1 if self._dev else 0,
            -1 if self._pre else 0,
            self._pre if self._pre else None,
        )

    @classmethod
    def from_string_version(cls, string_version: str) -> Optional['Version']:
        match = VERSION_REGEX.fullmatch(string_version)
        if not match:
            return None
        fields = match.groupdict()
        fields['base'] = tuple(map(int, fields['base'].split('.')))
        pre = fields['pre']
        if pre:
            if pre.startswith('rc'):
                fields['pre'] = ('rc', int(pre[2:]))
            else:
                fields['pre'] = (pre[0], int(pre[1:]))
        fields['dev'] = bool(fields['dev'])
        return cls(**fields)

    def __hash__(self) -> int:
        return self._hash

    __eq__ = Comparison()
    __ne__ = Comparison()
    __lt__ = Comparison()
    __le__ = Comparison()
    __gt__ = Comparison()
    __ge__ = Comparison()